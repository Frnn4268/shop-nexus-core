package repository

import (
	"auth-service/internal/models"
	"context"
	"errors"
	"log"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type UserRepository struct {
	collection *mongo.Collection
}

func NewUserRepository(db *mongo.Database) *UserRepository {
	collection := db.Collection("users")

	indexModel := mongo.IndexModel{
		Keys:    bson.D{{Key: "email", Value: 1}},
		Options: options.Index().SetUnique(true),
	}
	_, err := collection.Indexes().CreateOne(context.Background(), indexModel)
	if err != nil {
		log.Printf("Failed to create unique email index: %v", err)
	}

	return &UserRepository{collection: collection}
}

func (r *UserRepository) CreateUser(ctx context.Context, user *models.User) error {
	result, err := r.collection.InsertOne(ctx, user)
	if err != nil {
		return err
	}

	if oid, ok := result.InsertedID.(primitive.ObjectID); ok {
		user.ID = oid
	} else {
		return errors.New("unsupported value type for InsertedID")
	}

	return nil
}

func (r *UserRepository) FindUserByEmail(ctx context.Context, email string) (*models.User, error) {
	var user models.User
	err := r.collection.FindOne(ctx, bson.M{"email": email}).Decode(&user)
	if err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, nil
		}
		return nil, err
	}
	return &user, nil
}

func (r *UserRepository) FindUserByID(ctx context.Context, id string) (*models.User, error) {
	objID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return nil, err
	}

	var user models.User
	err = r.collection.FindOne(ctx, bson.M{"_id": objID}).Decode(&user)
	return &user, err
}

func (r *UserRepository) UpdateGoogleIdentity(ctx context.Context, userID primitive.ObjectID, subject string, name string) (*models.User, error) {
	update := bson.M{
		"$set": bson.M{
			"auth_provider": models.AuthProviderGoogle,
			"oauth_subject": subject,
			"name":          name,
		},
	}

	options := options.FindOneAndUpdate().SetReturnDocument(options.After)
	var user models.User
	if err := r.collection.FindOneAndUpdate(ctx, bson.M{"_id": userID}, update, options).Decode(&user); err != nil {
		return nil, err
	}

	return &user, nil
}
