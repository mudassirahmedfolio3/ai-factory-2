# Delivery backlog

## Epics
- **E-01** Authentication and Account Management (stories: US-001, US-002, US-003, US-016)
- **E-02** Product Catalog and Discovery (stories: US-004, US-005, US-006)
- **E-03** Shopping Cart (stories: US-007, US-008)
- **E-04** Checkout and Payment (stories: US-009, US-010, US-011)
- **E-05** Order Confirmation and History (stories: US-012, US-013, US-014)
- **E-06** Customer Support and Policy (stories: US-015)
- **E-07** Analytics and Tracking (stories: US-017)
- **E-08** Admin Product Management (stories: US-019, US-020)
- **E-09** Admin Stock Management (stories: US-021)
- **E-10** Admin Order Management (stories: US-022, US-023, US-024, US-025)
- **E-11** Admin Configuration (stories: US-026)
- **E-12** Admin Authentication (stories: US-018)

## M1: Infrastructure and Backend Foundation
Set up development infrastructure, database schema, backend project structure, authentication and authorization, API documentation.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Set up project infrastructure, CI/CD, and database | infra | 5 | - |  |
| WI-002 Design and implement shared domain models and error handling | shared | 3 | WI-001 |  |
| WI-003 Implement database schema for users, products, variants, orders, and audit logs | backend | 4 | WI-002 |  |
| WI-004 Implement password hashing, JWT tokens, and session management backend | backend | 3 | WI-003 | US-001, US-002 |
| WI-010 Create OpenAPI specification and API documentation | shared | 3 | WI-003 |  |
| WI-039 Implement backend request validation and error handling | backend | 3 | WI-003 |  |
| WI-040 Implement backend authorization checks for user data access | backend | 2 | WI-004 | US-002 |
| WI-041 Set up crash reporting and error monitoring backend | infra | 2 | WI-001 |  |

## M2: User Authentication and Account Management (Backend)
Implement user sign-up, sign-in, password reset, account deletion, session management with tests.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-005 Implement user sign-up and input validation backend API | backend | 2 | WI-004 | US-001 |
| WI-006 Implement user sign-in backend API | backend | 2 | WI-004 | US-002 |
| WI-007 Implement password reset email flow backend API | backend | 3 | WI-004 | US-003 |
| WI-008 Implement account deletion with data anonymization backend API | backend | 3 | WI-004 | US-016 |
| WI-009 Implement transactional email service integration | backend | 4 | WI-005 | US-003, US-012, US-014 |

## M3: Product Catalog and Discovery APIs (Backend)
Implement product and variant management, stock tracking, catalog browsing and search endpoints.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-011 Implement product catalog schema and CRUD backend API | backend | 3 | WI-003 | US-019 |
| WI-012 Implement variant management with stock tracking backend API | backend | 3 | WI-011 | US-019 |
| WI-013 Implement product photo upload and storage backend | backend | 3 | WI-011 | US-019 |
| WI-014 Implement CSV product catalog import backend API | backend | 4 | WI-012 | US-020 |
| WI-015 Implement stock spreadsheet import backend API | backend | 3 | WI-012 | US-021 |
| WI-016 Implement GET products catalog endpoint with pagination and filtering | backend | 3 | WI-012 | US-004, US-005, US-006 |
| WI-017 Implement GET product detail endpoint with variants and stock | backend | 2 | WI-012 | US-006 |
| WI-037 Implement admin shipping configuration backend API | backend | 2 | WI-003 | US-026 |

## M4: Analytics Logging and Consent (Backend)
Implement analytics event logging endpoint and event types for tracking.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-018 Implement analytics events logging backend API | backend | 2 | WI-004 | US-017 |

## M5: Cart Management APIs (Backend)
Implement cart storage, add to cart, remove from cart, quantity management endpoints.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-019 Implement cart storage and retrieval backend API | backend | 3 | WI-004 | US-007, US-008 |
| WI-020 Implement add to cart backend API with quantity management | backend | 2 | WI-019 | US-007 |
| WI-021 Implement cart item removal and update backend API | backend | 2 | WI-019 | US-008 |

## M6: Checkout and Stock Reservation (Backend)
Implement order creation with stock reservation, delivery address and shipping option selection, expiry job for releasing stock.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-022 Implement order creation with stock reservation backend API | backend | 4 | WI-020 | US-010 |
| WI-023 Implement delivery address and shipping option selection backend API | backend | 3 | WI-022 | US-009 |
| WI-026 Implement order expiry job for releasing reserved stock | backend | 3 | WI-022 | US-010 |

## M7: Payment Processing with Stripe (Backend)
Implement Stripe PaymentIntent creation and webhook handler for marking orders paid, idempotent payment processing.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-024 Implement Stripe PaymentIntent creation backend API | backend | 2 | WI-023 | US-011 |
| WI-025 Implement Stripe webhook handler for payment success | backend | 4 | WI-024 | US-011, US-012 |

## M8: Order Confirmation and History (Backend)
Implement order confirmation emails, order history endpoint, customer-facing status mapping, order detail retrieval.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-027 Implement order confirmation email backend | backend | 2 | WI-025 | US-012 |
| WI-028 Implement order history endpoint backend API | backend | 3 | WI-022 | US-013 |
| WI-029 Implement customer-facing order status mapping backend | backend | 2 | WI-028 | US-013 |
| WI-030 Implement order status update emails backend | backend | 2 | WI-009 | US-014 |

## M9: Admin Authentication and Order Management (Backend)
Implement admin sign-in, order list with filtering, status updates, cancellation, refund recording, audit logging.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-031 Implement admin sign-in backend API | backend | 2 | WI-004 | US-018 |
| WI-032 Implement admin order list and filter backend API | backend | 2 | WI-028 | US-022 |
| WI-033 Implement admin order status update backend API | backend | 3 | WI-032 | US-022, US-023, US-024 |
| WI-034 Implement admin order cancellation with stock release backend API | backend | 2 | WI-033 | US-023 |
| WI-035 Implement admin refund recording backend API | backend | 2 | WI-033 | US-024 |
| WI-036 Implement late payment handling for expired orders backend API | backend | 3 | WI-025 | US-025 |
| WI-038 Implement audit logging for all admin actions | backend | 3 | WI-003 | US-022, US-024 |

## M10: Backend Testing and Quality Assurance
Implement comprehensive unit and integration tests for all core flows, security review, performance optimization.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-089 Implement backend unit and integration tests for core flows | backend | 5 | WI-025 |  |
| WI-100 Performance testing and optimization for backend API | backend | 3 | WI-089 |  |
| WI-101 Security hardening and OWASP compliance review | backend | 4 | WI-039 |  |

## M11: Mobile App Setup and Navigation (Frontend)
Set up Flutter project, navigation structure, shared models, API client generation, analytics consent and tracking.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-042 Implement Flutter project structure and navigation setup | frontend | 3 | WI-001 |  |
| WI-043 Generate Dart API client from OpenAPI specification | shared | 2 | WI-010 |  |
| WI-044 Implement shared Dart models and freezed serialization | shared | 2 | WI-043 |  |
| WI-045 Implement analytics consent screen and storage mobile | frontend | 2 | WI-042 | US-017 |
| WI-046 Implement analytics event tracking mobile | frontend | 3 | WI-018 | US-017 |

## M12: User Authentication UI and Screens (Mobile)
Implement sign-up, sign-in, password reset, account deletion, sign-out, session persistence on mobile.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-047 Implement sign-up screen and form validation mobile | frontend | 2 | WI-042 | US-001 |
| WI-048 Implement sign-up logic and token storage mobile | frontend | 2 | WI-005 | US-001 |
| WI-049 Implement sign-in screen and form validation mobile | frontend | 2 | WI-042 | US-002 |
| WI-050 Implement sign-in logic and session persistence mobile | frontend | 3 | WI-006 | US-002 |
| WI-051 Implement sign-out functionality mobile | frontend | 1 | WI-050 | US-002 |
| WI-052 Implement password reset request screen mobile | frontend | 1 | WI-042 | US-003 |
| WI-053 Implement password reset completion from email link mobile | frontend | 3 | WI-007 | US-003 |
| WI-054 Implement account deletion flow mobile | frontend | 2 | WI-050 | US-016 |

## M13: Product Catalog and Discovery UI (Mobile)
Implement home screen, category browsing, product list with search, product detail screen with image loading.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-055 Implement home screen and category list mobile | frontend | 2 | WI-042 | US-004 |
| WI-056 Implement product list screen with pagination and search mobile | frontend | 3 | WI-016 | US-004, US-005 |
| WI-057 Implement search analytics event mobile | frontend | 1 | WI-046 | US-005 |
| WI-058 Implement product detail screen mobile | frontend | 3 | WI-017 | US-006 |
| WI-059 Implement product view analytics event mobile | frontend | 1 | WI-046 | US-006 |
| WI-060 Implement image loading and optimization mobile | frontend | 2 | WI-042 | US-004, US-006 |

## M14: Shopping Cart UI (Mobile)
Implement cart state management, add to cart flow, cart screen with item management, stock warnings.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-061 Implement cart state management with Riverpod mobile | frontend | 3 | WI-044 | US-007, US-008 |
| WI-062 Implement add to cart with quantity selection mobile | frontend | 2 | WI-020 | US-007 |
| WI-063 Implement add to cart analytics event mobile | frontend | 1 | WI-046 | US-007 |
| WI-064 Implement cart screen with item management mobile | frontend | 3 | WI-061 | US-008 |
| WI-065 Implement remove from cart analytics event mobile | frontend | 1 | WI-046 | US-008 |
| WI-066 Implement stock status warning in cart mobile | frontend | 2 | WI-064 | US-008 |

## M15: Checkout and Delivery (Mobile)
Implement checkout flow entry, delivery address entry, shipping option selection, order summary review.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-067 Implement checkout flow entry and cart validation mobile | frontend | 2 | WI-062 | US-009 |
| WI-068 Implement delivery address entry screen mobile | frontend | 2 | WI-042 | US-009 |
| WI-069 Implement shipping option selection and cost calculation mobile | frontend | 2 | WI-068 | US-009 |
| WI-070 Implement order summary review screen mobile | frontend | 2 | WI-069 | US-009 |

## M16: Payment and Order Confirmation (Mobile)
Implement stock reservation, Stripe payment integration, payment flow, confirmation screen, order history and detail.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-071 Implement checkout stock reservation mobile | frontend | 2 | WI-022 | US-010 |
| WI-072 Implement checkout analytics event mobile | frontend | 1 | WI-046 | US-010 |
| WI-073 Integrate Stripe SDK and PaymentIntent confirmation mobile | frontend | 3 | WI-042 | US-011 |
| WI-074 Implement payment flow and intent creation mobile | frontend | 3 | WI-024 | US-011 |
| WI-075 Implement payment success analytics event mobile | frontend | 1 | WI-046 | US-011 |
| WI-076 Implement payment failure handling mobile | frontend | 2 | WI-074 | US-011 |
| WI-077 Implement order confirmation screen mobile | frontend | 2 | WI-074 | US-012 |
| WI-078 Implement order placed analytics event mobile | frontend | 1 | WI-046 | US-012 |
| WI-079 Implement order history screen mobile | frontend | 2 | WI-028 | US-013 |
| WI-080 Implement order detail screen mobile | frontend | 3 | WI-029 | US-013 |

## M17: Customer Support and Settings (Mobile)
Implement returns policy, settings menu, account management, legal pages, analytics consent management.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-081 Implement returns policy static page mobile | frontend | 1 | WI-042 | US-015 |
| WI-082 Implement settings menu and account management mobile | frontend | 2 | WI-050 | US-016 |
| WI-083 Implement privacy policy and legal pages mobile | frontend | 1 | WI-082 |  |

## M18: Mobile Build Configuration and Testing
Configure Android and iOS builds, set up mobile unit and integration tests, performance and accessibility optimization.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-084 Implement Android build configuration and signing | infra | 2 | WI-042 |  |
| WI-085 Implement iOS build configuration and signing | infra | 2 | WI-042 |  |
| WI-087 Set up GitHub Actions CI/CD for Android build and release | infra | 3 | WI-084 |  |
| WI-088 Set up GitHub Actions CI/CD for iOS build and release | infra | 3 | WI-085 |  |
| WI-090 Implement mobile unit and widget tests for screens and logic | frontend | 4 | WI-074 |  |
| WI-091 Implement mobile integration tests for end-to-end checkout flow | frontend | 5 | WI-086 |  |
| WI-099 Performance testing and optimization for mobile app | frontend | 4 | WI-091 |  |
| WI-102 Accessibility testing and improvements (WCAG 2.1 AA) | frontend | 3 | WI-091 |  |

## M19: Admin Web Back-office Product Management
Implement admin authentication, product CRUD, photo upload, CSV import, stock import, shipping configuration.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-092 Implement admin web back-office home and product management UI | frontend | 4 | WI-011 | US-019 |
| WI-093 Implement admin CSV product import UI and flow | frontend | 2 | WI-014 | US-020 |
| WI-094 Implement admin stock import UI and flow | frontend | 2 | WI-015 | US-021 |
| WI-097 Implement admin shipping configuration UI | frontend | 1 | WI-037 | US-026 |
| WI-098 Implement admin sign-in page and authentication UI | frontend | 1 | WI-031 | US-018 |

## M20: Admin Web Back-office Order and Audit Management
Implement admin order list, status updates, cancellation, refund recording, audit log viewing.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-095 Implement admin order management UI with filtering and status updates | frontend | 3 | WI-032 | US-022, US-023 |
| WI-096 Implement admin audit log UI | frontend | 2 | WI-038 | US-022 |

## M21: Production Deployment and Go-Live Preparation
Set up production database, deployment pipeline, monitoring, logging, Stripe live configuration, staging acceptance testing.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-086 Configure staging environment with test database and Stripe test keys | infra | 2 | WI-001 |  |
| WI-103 Set up production PostgreSQL database with backups and monitoring | infra | 2 | WI-001 |  |
| WI-104 Set up production backend deployment with monitoring and logging | infra | 3 | WI-041 |  |
| WI-105 Prepare for production Stripe configuration | infra | 2 | WI-024 |  |
| WI-106 Staging acceptance testing and bug fixes | frontend | 5 | WI-091 |  |
