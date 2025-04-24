package middleware

import (
	"github.com/gin-gonic/gin"
	"github.com/ulule/limiter/v3"
	ginmw "github.com/ulule/limiter/v3/drivers/middleware/gin"
	"github.com/ulule/limiter/v3/drivers/store/memory"
)

func RateLimiter(rateLimit string) gin.HandlerFunc {
	rate, err := limiter.NewRateFromFormatted(rateLimit)
	if err != nil {
		panic(err)
	}

	store := memory.NewStore()
	instance := limiter.New(store, rate)
	return ginmw.NewMiddleware(instance)
}
