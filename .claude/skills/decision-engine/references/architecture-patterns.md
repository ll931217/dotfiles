# Architecture Pattern Selection Guide

Guidelines for selecting appropriate architectural patterns based on complexity and requirements.

## Pattern Selection Matrix

| Pattern | Complexity | Use When | Avoid When |
|---------|------------|----------|------------|
| **Simple Function** | Low | Single responsibility, no state | Multiple responsibilities |
| **Service Layer** | Medium | Business logic, data access | Trivial CRUD |
| **Repository** | Medium | Data access abstraction | Simple queries |
| **Factory** | Low-Medium | Object creation, variants | Single object type |
| **Strategy** | Medium | Multiple algorithms, interchangeable | Fixed algorithm |
| **Middleware** | Medium | Request/response pipeline | Simple transformations |
| **Observer** | Medium | Event-driven, loose coupling | Tight coupling acceptable |
| **Decorator** | Low-Medium | Add behavior dynamically | Static behavior |

## Pattern Descriptions

### Simple Function

**Use for:** Single-purpose, stateless operations

**Example:** Password hashing, token generation

```javascript
// Simple function - no pattern needed
function hashPassword(password) {
  return bcrypt.hash(password, 10);
}
```

**Indicators:**
- Single input → single output
- No side effects
- No state management
- Reusable across contexts

### Service Layer

**Use for:** Business logic, coordination between components

**Example:** User registration, order processing

```javascript
// Service layer
class AuthService {
  constructor(userRepo, emailService) {
    this.userRepo = userRepo;
    this.emailService = emailService;
  }

  async register(email, password) {
    const hash = await hashPassword(password);
    const user = await this.userRepo.create(email, hash);
    await this.emailService.sendVerification(user.email);
    return user;
  }
}
```

**Indicators:**
- Multiple operations coordinated
- Business rules enforced
- Cross-component communication
- Transactional operations

### Repository Pattern

**Use for:** Data access abstraction

**Example:** User CRUD, database queries

```javascript
// Repository
class UserRepository {
  async findById(id) { /* ... */ }
  async findByEmail(email) { /* ... */ }
  async create(user) { /* ... */ }
  async update(user) { /* ... */ }
  async delete(id) { /* ... */ }
}
```

**Indicators:**
- Database operations
- Multiple data sources
- Query abstraction needed
- Testing requires mocking

### Factory Pattern

**Use for:** Creating objects with variants

**Example:** Payment processors, notification channels

```javascript
// Factory
class PaymentProcessorFactory {
  create(type) {
    switch(type) {
      case 'stripe': return new StripeProcessor();
      case 'paypal': return new PayPalProcessor();
      default: throw new Error('Unknown type');
    }
  }
}
```

**Indicators:**
- Object type determined at runtime
- Multiple object variants
- Complex initialization logic
- Future extensibility needed

### Strategy Pattern

**Use for:** Interchangeable algorithms

**Example:** Sorting algorithms, compression methods

```javascript
// Strategy
class CompressionStrategy {
  setStrategy(strategy) {
    this.strategy = strategy;
  }

  compress(data) {
    return this.strategy.compress(data);
  }
}
```

**Indicators:**
- Multiple valid algorithms
- Runtime algorithm selection
- Algorithm varies by context
- Testing different approaches

### Middleware Pattern

**Use for:** Request/response pipeline processing

**Example:** Authentication, logging, rate limiting

```javascript
// Middleware
app.use((req, res, next) => {
  console.log(req.method, req.url);
  next();
});
```

**Indicators:**
- Sequential processing steps
- Request/response transformation
- Cross-cutting concerns
- Composable operations

### Observer Pattern

**Use for:** Event-driven updates, loose coupling

**Example:** User notifications, cache invalidation

```javascript
// Observer
class EventEmitter {
  on(event, callback) { /* ... */ }
  emit(event, data) { /* ... */ }
}
```

**Indicators:**
- One-to-many communication
- Loose coupling required
- Event-driven behavior
- Asynchronous updates

### Decorator Pattern

**Use for:** Adding behavior dynamically

**Example:** Caching, validation, logging

```javascript
// Decorator
function withCache(fn) {
  return async (...args) => {
    const cached = cache.get(args);
    if (cached) return cached;
    const result = await fn(...args);
    cache.set(args, result);
    return result;
  };
}
```

**Indicators:**
- Add behavior without modification
- Composable enhancements
- Runtime decoration
- Separation of concerns

## Complexity Assessment

### Low Complexity (Simple Function)

**Characteristics:**
- Single responsibility
- No external dependencies
- Pure function (no side effects)
- <20 lines of code

**Examples:**
- Data validation
- Format conversion
- Calculation functions

### Medium Complexity (Service/Repository/Factory)

**Characteristics:**
- Multiple responsibilities
- External dependencies
- State management
- 20-100 lines of code

**Examples:**
- CRUD operations
- Business logic
- Data access

### High Complexity (Multiple Patterns)

**Characteristics:**
- Complex interactions
- Multiple patterns combined
- Significant state
- 100+ lines of code

**Examples:**
- Workflow orchestration
- Complex business rules
- Multi-component systems

## Decision Tree

```
Need to process data?
├─ Yes, single transformation → Simple Function
└─ Yes, multiple steps → Service Layer

Need to access data?
├─ Yes, simple queries → Simple Function / Repository
└─ Yes, complex queries → Repository

Need to create objects?
├─ Yes, single type → Constructor
├─ Yes, multiple types → Factory
└─ Yes, complex creation → Builder

Need to vary algorithm?
├─ Yes, runtime selection → Strategy
└─ No, fixed algorithm → Simple Function

Need to process requests?
├─ Yes, sequential pipeline → Middleware
└─ No, direct handling → Service Layer

Need event-driven updates?
├─ Yes, one-to-many → Observer
└─ No, direct calls → Simple Function / Service Layer

Need to add behavior dynamically?
├─ Yes, compose at runtime → Decorator
└─ No, static behavior → Direct implementation
```

## Pattern Matching with Existing Codebase

Before selecting a pattern:

1. **Detect existing patterns** - Use `scripts/detect_patterns.py`
2. **Match to context** - What patterns are already used?
3. **Follow conventions** - Prefer existing patterns over new ones
4. **Consider complexity** - Don't over-engineer simple features

**Example:**
- Codebase has service layer → Use service pattern for new features
- Codebase uses repositories → Create repository for new data access
- Codebase has no patterns → Start simple, add patterns as needed
