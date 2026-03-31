package health

import "context"

type CheckFunc func(context.Context) error

type Checker struct {
	service string
	checks  map[string]CheckFunc
}

type Result struct {
	Service      string            `json:"service"`
	Status       string            `json:"status"`
	Dependencies map[string]string `json:"dependencies"`
}

func NewChecker(service string, checks map[string]CheckFunc) *Checker {
	return &Checker{service: service, checks: checks}
}

func (c *Checker) Check(ctx context.Context) Result {
	result := Result{
		Service:      c.service,
		Status:       "ok",
		Dependencies: make(map[string]string, len(c.checks)),
	}

	for name, check := range c.checks {
		if check == nil {
			result.Dependencies[name] = "skipped"
			continue
		}

		if err := check(ctx); err != nil {
			result.Status = "error"
			result.Dependencies[name] = err.Error()
			continue
		}

		result.Dependencies[name] = "ok"
	}

	return result
}

func (c *Checker) Healthy(ctx context.Context) bool {
	return c.Check(ctx).Status == "ok"
}
