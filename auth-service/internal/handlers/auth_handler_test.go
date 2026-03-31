package handlers

import (
	"auth-service/internal/models"
	"auth-service/internal/services"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"golang.org/x/crypto/bcrypt"
)

type fakeUserStore struct {
	byEmail      map[string]*models.User
	byID         map[string]*models.User
	createdUsers []*models.User
	createErr    error
	findErr      error
	updateErr    error
}

func newFakeUserStore() *fakeUserStore {
	return &fakeUserStore{
		byEmail: make(map[string]*models.User),
		byID:    make(map[string]*models.User),
	}
}

func (f *fakeUserStore) CreateUser(_ context.Context, user *models.User) error {
	if f.createErr != nil {
		return f.createErr
	}

	clone := *user
	if clone.ID.IsZero() {
		clone.ID = primitive.NewObjectID()
	}
	*user = clone
	f.byEmail[clone.Email] = &clone
	f.byID[clone.ID.Hex()] = &clone
	f.createdUsers = append(f.createdUsers, &clone)
	return nil
}

func (f *fakeUserStore) FindUserByEmail(_ context.Context, email string) (*models.User, error) {
	if f.findErr != nil {
		return nil, f.findErr
	}
	user, ok := f.byEmail[email]
	if !ok {
		return nil, nil
	}
	clone := *user
	return &clone, nil
}

func (f *fakeUserStore) FindUserByID(_ context.Context, id string) (*models.User, error) {
	user, ok := f.byID[id]
	if !ok {
		return nil, errors.New("user not found")
	}
	clone := *user
	return &clone, nil
}

func (f *fakeUserStore) UpdateGoogleIdentity(_ context.Context, userID primitive.ObjectID, subject string, name string) (*models.User, error) {
	if f.updateErr != nil {
		return nil, f.updateErr
	}

	user, ok := f.byID[userID.Hex()]
	if !ok {
		return nil, errors.New("user not found")
	}

	user.AuthProvider = models.AuthProviderGoogle
	user.OAuthSubject = subject
	user.Name = name
	clone := *user
	return &clone, nil
}

type fakeGoogleVerifier struct {
	identity *services.GoogleIdentity
	err      error
}

func (f *fakeGoogleVerifier) VerifyIDToken(_ context.Context, _ string) (*services.GoogleIdentity, error) {
	if f.err != nil {
		return nil, f.err
	}
	return f.identity, nil
}

func TestRegisterCreatesLocalUserWithDefaultRole(t *testing.T) {
	gin.SetMode(gin.TestMode)
	repo := newFakeUserStore()
	handler := NewAuthHandlerWithDependencies(repo, "secret", time.Hour, nil)

	recorder := httptest.NewRecorder()
	ctx, router := gin.CreateTestContext(recorder)
	router.POST("/auth/register", handler.Register)

	body := map[string]any{
		"name":         "John",
		"email":        "john@example.com",
		"password":     "supersecret",
		"phone_number": "123456789",
	}
	request := newJSONRequest(t, http.MethodPost, "/auth/register", body)
	ctx.Request = request
	router.HandleContext(ctx)

	if recorder.Code != http.StatusCreated {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusCreated, recorder.Code, recorder.Body.String())
	}

	if len(repo.createdUsers) != 1 {
		t.Fatalf("expected one created user, got %d", len(repo.createdUsers))
	}

	created := repo.createdUsers[0]
	if created.AuthProvider != models.AuthProviderLocal {
		t.Fatalf("expected auth provider %q, got %q", models.AuthProviderLocal, created.AuthProvider)
	}
	if len(created.Roles) != 1 || created.Roles[0] != models.RoleUser {
		t.Fatalf("expected default user role, got %#v", created.Roles)
	}
	if created.Password == "supersecret" {
		t.Fatal("expected password to be hashed before persistence")
	}
	if err := bcrypt.CompareHashAndPassword([]byte(created.Password), []byte("supersecret")); err != nil {
		t.Fatalf("expected stored password hash to match original password: %v", err)
	}
}

func TestLoginReturnsJWTForValidCredentials(t *testing.T) {
	gin.SetMode(gin.TestMode)
	repo := newFakeUserStore()
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte("supersecret"), bcrypt.DefaultCost)
	if err != nil {
		t.Fatalf("failed to hash password: %v", err)
	}
	user := &models.User{
		ID:       primitive.NewObjectID(),
		Name:     "John",
		Email:    "john@example.com",
		Password: string(hashedPassword),
		Roles:    []models.Role{models.RoleUser},
	}
	repo.byEmail[user.Email] = user
	repo.byID[user.ID.Hex()] = user

	handler := NewAuthHandlerWithDependencies(repo, "secret", time.Hour, nil)
	recorder := httptest.NewRecorder()
	ctx, router := gin.CreateTestContext(recorder)
	router.POST("/auth/login", handler.Login)
	ctx.Request = newJSONRequest(t, http.MethodPost, "/auth/login", map[string]string{
		"email":    user.Email,
		"password": "supersecret",
	})
	router.HandleContext(ctx)

	if recorder.Code != http.StatusOK {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusOK, recorder.Code, recorder.Body.String())
	}

	var payload map[string]string
	if err := json.Unmarshal(recorder.Body.Bytes(), &payload); err != nil {
		t.Fatalf("failed to decode login response: %v", err)
	}
	if payload["token"] == "" {
		t.Fatal("expected login response to include a token")
	}
}

func TestGoogleLoginCreatesGoogleUserWhenEmailDoesNotExist(t *testing.T) {
	gin.SetMode(gin.TestMode)
	repo := newFakeUserStore()
	verifier := &fakeGoogleVerifier{identity: &services.GoogleIdentity{
		Subject: "google-subject-1",
		Email:   "john@example.com",
		Name:    "John",
	}}
	handler := NewAuthHandlerWithDependencies(repo, "secret", time.Hour, verifier)

	recorder := httptest.NewRecorder()
	ctx, router := gin.CreateTestContext(recorder)
	router.POST("/auth/google", handler.LoginWithGoogle)
	ctx.Request = newJSONRequest(t, http.MethodPost, "/auth/google", map[string]string{"id_token": "google-token"})
	router.HandleContext(ctx)

	if recorder.Code != http.StatusOK {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusOK, recorder.Code, recorder.Body.String())
	}

	if len(repo.createdUsers) != 1 {
		t.Fatalf("expected one created Google user, got %d", len(repo.createdUsers))
	}

	created := repo.createdUsers[0]
	if created.AuthProvider != models.AuthProviderGoogle {
		t.Fatalf("expected auth provider %q, got %q", models.AuthProviderGoogle, created.AuthProvider)
	}
	if created.OAuthSubject != "google-subject-1" {
		t.Fatalf("expected OAuth subject to be persisted, got %q", created.OAuthSubject)
	}
}

func TestGoogleLoginRejectsExistingPasswordAccount(t *testing.T) {
	gin.SetMode(gin.TestMode)
	repo := newFakeUserStore()
	user := &models.User{
		ID:           primitive.NewObjectID(),
		Name:         "John",
		Email:        "john@example.com",
		AuthProvider: models.AuthProviderLocal,
	}
	repo.byEmail[user.Email] = user
	repo.byID[user.ID.Hex()] = user

	verifier := &fakeGoogleVerifier{identity: &services.GoogleIdentity{
		Subject: "google-subject-1",
		Email:   user.Email,
		Name:    user.Name,
	}}
	handler := NewAuthHandlerWithDependencies(repo, "secret", time.Hour, verifier)

	recorder := httptest.NewRecorder()
	ctx, router := gin.CreateTestContext(recorder)
	router.POST("/auth/google", handler.LoginWithGoogle)
	ctx.Request = newJSONRequest(t, http.MethodPost, "/auth/google", map[string]string{"id_token": "google-token"})
	router.HandleContext(ctx)

	if recorder.Code != http.StatusConflict {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusConflict, recorder.Code, recorder.Body.String())
	}
}

func newJSONRequest(t *testing.T, method string, target string, payload any) *http.Request {
	t.Helper()
	body, err := json.Marshal(payload)
	if err != nil {
		t.Fatalf("failed to marshal payload: %v", err)
	}

	request := httptest.NewRequest(method, target, bytes.NewReader(body))
	request.Header.Set("Content-Type", "application/json")
	return request
}
