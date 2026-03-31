package services

import (
	"context"
	"fmt"
	"strings"
	"sync"

	"github.com/coreos/go-oidc/v3/oidc"
)

type GoogleIdentity struct {
	Subject string
	Email   string
	Name    string
}

type GoogleVerifier interface {
	VerifyIDToken(ctx context.Context, rawToken string) (*GoogleIdentity, error)
}

type googleVerifier struct {
	clientID string
	once     sync.Once
	verifier *oidc.IDTokenVerifier
	initErr  error
}

func NewGoogleVerifier(clientID string) GoogleVerifier {
	if strings.TrimSpace(clientID) == "" {
		return nil
	}

	return &googleVerifier{clientID: clientID}
}

func (g *googleVerifier) VerifyIDToken(ctx context.Context, rawToken string) (*GoogleIdentity, error) {
	if strings.TrimSpace(rawToken) == "" {
		return nil, fmt.Errorf("id token is required")
	}

	verifier, err := g.getVerifier(ctx)
	if err != nil {
		return nil, err
	}

	token, err := verifier.Verify(ctx, rawToken)
	if err != nil {
		return nil, fmt.Errorf("invalid Google ID token: %w", err)
	}

	var claims struct {
		Email         string `json:"email"`
		Name          string `json:"name"`
		EmailVerified bool   `json:"email_verified"`
	}
	if err := token.Claims(&claims); err != nil {
		return nil, fmt.Errorf("failed to parse Google token claims: %w", err)
	}

	email := claims.Email
	name := claims.Name
	verified := claims.EmailVerified
	if !verified {
		return nil, fmt.Errorf("Google account email is not verified")
	}
	if email == "" {
		return nil, fmt.Errorf("Google account email is missing")
	}

	if name == "" {
		name = strings.Split(email, "@")[0]
	}

	return &GoogleIdentity{
		Subject: token.Subject,
		Email:   email,
		Name:    name,
	}, nil
}

func (g *googleVerifier) getVerifier(ctx context.Context) (*oidc.IDTokenVerifier, error) {
	g.once.Do(func() {
		provider, err := oidc.NewProvider(ctx, "https://accounts.google.com")
		if err != nil {
			g.initErr = fmt.Errorf("failed to initialize Google OIDC provider: %w", err)
			return
		}

		g.verifier = provider.Verifier(&oidc.Config{ClientID: g.clientID})
	})

	if g.initErr != nil {
		return nil, g.initErr
	}

	if g.verifier == nil {
		return nil, fmt.Errorf("Google OIDC verifier is not available")
	}

	return g.verifier, nil
}
