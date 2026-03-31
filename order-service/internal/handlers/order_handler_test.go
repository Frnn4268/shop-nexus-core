package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"order-service/internal/handlers/events"
	"order-service/internal/models"
	"order-service/internal/services/payment"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

type fakeOrderStore struct {
	createdOrders []*models.Order
	orders        map[string]*models.Order
	createErr     error
	getAllErr     error
	getByIDErr    error
}

func newFakeOrderStore() *fakeOrderStore {
	return &fakeOrderStore{orders: make(map[string]*models.Order)}
}

func (f *fakeOrderStore) CreateOrder(_ context.Context, order *models.Order) error {
	if f.createErr != nil {
		return f.createErr
	}
	clone := *order
	if clone.ID.IsZero() {
		clone.ID = primitive.NewObjectID()
	}
	*order = clone
	f.createdOrders = append(f.createdOrders, &clone)
	f.orders[clone.ID.Hex()] = &clone
	return nil
}

func (f *fakeOrderStore) GetAllOrders(_ context.Context) ([]models.Order, error) {
	if f.getAllErr != nil {
		return nil, f.getAllErr
	}
	orders := make([]models.Order, 0, len(f.orders))
	for _, order := range f.orders {
		orders = append(orders, *order)
	}
	return orders, nil
}

func (f *fakeOrderStore) GetOrderByID(_ context.Context, id string) (*models.Order, error) {
	if f.getByIDErr != nil {
		return nil, f.getByIDErr
	}
	order, ok := f.orders[id]
	if !ok {
		return nil, errors.New("order not found")
	}
	clone := *order
	return &clone, nil
}

type fakePaymentProcessor struct {
	response payment.Response
	amounts  []float64
}

func (f *fakePaymentProcessor) Process(amount float64) payment.Response {
	f.amounts = append(f.amounts, amount)
	return f.response
}

type fakeOrderEventPublisher struct {
	published []interface{}
	err       error
}

func (f *fakeOrderEventPublisher) PublishOrderCreated(order interface{}) error {
	if f.err != nil {
		return f.err
	}
	f.published = append(f.published, order)
	return nil
}

func TestCreateOrderCalculatesTotalPersistsOrderAndPublishesEvent(t *testing.T) {
	gin.SetMode(gin.TestMode)
	repo := newFakeOrderStore()
	paymentProcessor := &fakePaymentProcessor{response: payment.Response{Success: true, PaymentID: "pay-1"}}
	publisher := &fakeOrderEventPublisher{}
	handler := NewOrderHandlerWithDependencies(repo, paymentProcessor, publisher)

	userID := primitive.NewObjectID()
	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Request = newOrderJSONRequest(t, http.MethodPost, "/orders", models.Order{
		Items: []models.OrderItem{{ProductID: "product-1", Quantity: 2, Price: 15.5}},
	})
	ctx.Set("claims", jwt.MapClaims{"user_id": userID.Hex()})

	handler.CreateOrder(ctx)

	if recorder.Code != http.StatusCreated {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusCreated, recorder.Code, recorder.Body.String())
	}

	if len(repo.createdOrders) != 1 {
		t.Fatalf("expected one persisted order, got %d", len(repo.createdOrders))
	}
	persisted := repo.createdOrders[0]
	if persisted.UserID != userID {
		t.Fatalf("expected order user id %s, got %s", userID.Hex(), persisted.UserID.Hex())
	}
	if persisted.Total != 31 {
		t.Fatalf("expected total 31, got %v", persisted.Total)
	}
	if persisted.Status != models.StatusCompleted {
		t.Fatalf("expected status %q, got %q", models.StatusCompleted, persisted.Status)
	}
	if len(paymentProcessor.amounts) != 1 || paymentProcessor.amounts[0] != 31 {
		t.Fatalf("expected payment to be processed for total 31, got %#v", paymentProcessor.amounts)
	}
	if len(publisher.published) != 1 {
		t.Fatalf("expected one published event, got %d", len(publisher.published))
	}
	publishedEvent, ok := publisher.published[0].(events.OrderCreatedEvent)
	if !ok {
		t.Fatalf("expected published payload to be OrderCreatedEvent, got %T", publisher.published[0])
	}
	if publishedEvent.EventType != events.OrderCreatedEventType {
		t.Fatalf("expected event type %q, got %q", events.OrderCreatedEventType, publishedEvent.EventType)
	}
	if publishedEvent.Data.OrderID == "" || publishedEvent.Data.UserID != userID.Hex() {
		t.Fatalf("expected event payload to include order and user identity, got %#v", publishedEvent.Data)
	}
}

func TestCreateOrderRejectsMissingClaims(t *testing.T) {
	gin.SetMode(gin.TestMode)
	handler := NewOrderHandlerWithDependencies(newFakeOrderStore(), &fakePaymentProcessor{}, &fakeOrderEventPublisher{})

	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Request = newOrderJSONRequest(t, http.MethodPost, "/orders", models.Order{
		Items: []models.OrderItem{{ProductID: "product-1", Quantity: 1, Price: 10}},
	})

	handler.CreateOrder(ctx)

	if recorder.Code != http.StatusUnauthorized {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusUnauthorized, recorder.Code, recorder.Body.String())
	}
}

func TestCreateOrderRejectsFailedPayment(t *testing.T) {
	gin.SetMode(gin.TestMode)
	repo := newFakeOrderStore()
	paymentProcessor := &fakePaymentProcessor{response: payment.Response{Success: false}}
	handler := NewOrderHandlerWithDependencies(repo, paymentProcessor, &fakeOrderEventPublisher{})

	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Request = newOrderJSONRequest(t, http.MethodPost, "/orders", models.Order{
		Items: []models.OrderItem{{ProductID: "product-1", Quantity: 1, Price: 10}},
	})
	ctx.Set("claims", jwt.MapClaims{"user_id": primitive.NewObjectID().Hex()})

	handler.CreateOrder(ctx)

	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusBadRequest, recorder.Code, recorder.Body.String())
	}
	if len(repo.createdOrders) != 0 {
		t.Fatalf("expected no persisted orders when payment fails, got %d", len(repo.createdOrders))
	}
}

func TestGetOrderByIDReturnsNotFoundWhenRepositoryFails(t *testing.T) {
	gin.SetMode(gin.TestMode)
	repo := newFakeOrderStore()
	repo.getByIDErr = errors.New("order not found")
	handler := NewOrderHandlerWithDependencies(repo, &fakePaymentProcessor{}, &fakeOrderEventPublisher{})

	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Params = gin.Params{{Key: "id", Value: primitive.NewObjectID().Hex()}}
	ctx.Request = httptest.NewRequest(http.MethodGet, "/orders/missing", nil)

	handler.GetOrderByID(ctx)

	if recorder.Code != http.StatusNotFound {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusNotFound, recorder.Code, recorder.Body.String())
	}
}

func newOrderJSONRequest(t *testing.T, method string, target string, payload any) *http.Request {
	t.Helper()
	body, err := json.Marshal(payload)
	if err != nil {
		t.Fatalf("failed to marshal payload: %v", err)
	}

	request := httptest.NewRequest(method, target, bytes.NewReader(body))
	request.Header.Set("Content-Type", "application/json")
	return request
}
