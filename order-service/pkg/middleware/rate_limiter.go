package middleware

import (
	"log"

	"github.com/gin-gonic/gin"
	"github.com/ulule/limiter/v3"
	ginmw "github.com/ulule/limiter/v3/drivers/middleware/gin"
	"github.com/ulule/limiter/v3/drivers/store/memory"
)

func RateLimiter(rateLimit string) gin.HandlerFunc {
    rate, err := limiter.NewRateFromFormatted(rateLimit)
    if err != nil {
        log.Printf("invalid rate limit %q, using fallback 100-M", rateLimit)
        rate, _ = limiter.NewRateFromFormatted("100-M")
    }

	store := memory.NewStore()
	limiterInstance := limiter.New(store, rate)
	return ginmw.NewMiddleware(limiterInstance)
}