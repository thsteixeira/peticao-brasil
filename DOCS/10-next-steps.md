# Next Steps - Democracia Direta

**Current Status:** 10 of 22 steps completed (45%)

## ✅ Completed (Steps 1-10)

- ✅ Django project structure with modular settings
- ✅ Data models (Petitions, Signatures, Categories)
- ✅ Authentication system (register, login, logout, profile)
- ✅ Petition CRUD with search/filter/sort
- ✅ PDF generation with ReportLab
- ✅ ICP-Brasil digital signature verification with PKCS#7 support
- ✅ File upload with security validation
- ✅ Sanitization and XSS/SQL injection protection
- ✅ Rate limiting on critical forms
- ✅ Celery configured for development (eager mode)

## 📋 Next Steps

### Step 11: Cloudflare Turnstile CAPTCHA Integration
**Priority:** High  
**Estimated Time:** 4-6 hours

**Objectives:**
- Protect forms against bots (registration, petition creation, signature)
- Integrate Cloudflare Turnstile (modern reCAPTCHA alternative)
- Implement server-side token validation

**Tasks:**
1. Create Cloudflare account and obtain Turnstile keys
2. Add Turnstile widget to templates
3. Create server-side token validator
4. Add verification to forms.py (SignatureSubmissionForm, UserCreationForm, PetitionForm)
5. Configure additional rate limiting for bypass attempts
6. Test with bots and real users

**Files to Modify:**
- `config/settings/base.py` - add TURNSTILE_SECRET_KEY
- `apps/core/validators.py` - create validate_turnstile_token()
- `templates/base.html` - include Turnstile script
- `apps/signatures/forms.py` - add CAPTCHA validation
- `apps/petitions/forms.py` - add CAPTCHA validation
- `apps/users/forms.py` - add CAPTCHA validation

---

### Step 12: Celery Configuration for Production
**Priority:** High  
**Estimated Time:** 6-8 hours

**Objectives:**
- Configure Redis as broker for production
- Configure worker and beat scheduler
- Implement task monitoring
- Configure retry policies and error handling

**Tasks:**
1. Configure Redis on Heroku (addon)
2. Create Procfile for worker and beat
3. Implement health checks for Celery
4. Configure Celery Beat for periodic tasks:
   - Pending signature verification (every 5 min)
   - Expired petition cleanup (daily)
   - Batch email sending (every 15 min)
5. Implement task monitoring with django-celery-results
6. Configure dead letter queue for failed tasks
7. Add detailed logging

**Files to Modify:**
- `config/settings/production.py` - configure CELERY_BROKER_URL
- `Procfile` - add worker and beat
- `apps/signatures/tasks.py` - improve error handling
- `apps/core/tasks.py` - create periodic tasks
- `requirements/production.txt` - add redis and django-celery-results

---

### Step 13: Email Notification System
**Priority:** High  
**Estimated Time:** 8-10 hours

**Objectives:**
- Send registration confirmations
- Notify about verified/rejected signatures
- Alert creators about signature milestones
- Send reminders for petitions nearing deadline

**Tasks:**
1. Configure SendGrid or Amazon SES for production
2. Create responsive HTML email templates:
   - Registration confirmation
   - Signature verified
   - Signature rejected (with reason)
   - Signature goal reached (25%, 50%, 75%, 100%)
   - Petition nearing deadline (7 days, 3 days, 1 day)
   - Petition published successfully
3. Implement email preference system
4. Create Celery tasks for async sending
5. Implement unsubscribe tokens
6. Add throttling to prevent spam
7. Logging of sent/failed emails

**Files to Create:**
- `apps/core/email.py` - email utilities
- `apps/core/tasks.py` - email sending tasks
- `templates/emails/` - HTML templates
- `apps/users/models.py` - add EmailPreference model

**Files to Modify:**
- `config/settings/production.py` - configure EMAIL_BACKEND
- `apps/signatures/tasks.py` - send notifications
- `apps/petitions/models.py` - add send_milestone_notification() method

---

### Step 14: Admin Moderation Interface
**Priority:** Medium-High  
**Estimated Time:** 6-8 hours

**Objectives:**
- Customized dashboard for moderators
- Review automatically rejected signatures
- Moderate petitions before publication
- Manage flagged content

**Tasks:**
1. Customize Django Admin with modern interface
2. Create dashboard with statistics:
   - Signatures pending manual review
   - Petitions awaiting approval
   - Signature rejection rate
   - Most popular petitions
3. Add bulk actions:
   - Approve/reject multiple signatures
   - Archive petitions
4. Implement reporting system
5. Add filters and advanced search
6. Create moderation action logs
7. Implement granular permissions (moderator vs admin)

**Files to Modify:**
- `apps/signatures/admin.py` - customize interface
- `apps/petitions/admin.py` - add moderation actions
- `apps/core/models.py` - create ModerationLog model
- `templates/admin/` - custom templates

---

### Step 15: Advanced Search and Filters
**Priority:** Medium  
**Estimated Time:** 8-10 hours

**Objectives:**
- Full-text search in petitions
- Combined filters (category + status + date + popularity)
- Sort by relevance, date, popularity
- Search suggestions (typeahead)

**Tasks:**
1. Implement PostgreSQL full-text search (SearchVector)
2. Create GIN indexes for performance
3. Add advanced filters to interface:
   - Multiple categories (OR)
   - Date range
   - Minimum signature count
   - Status (active, closed, goal reached)
4. Implement sorting by:
   - Relevance (search rank)
   - Most recent
   - Most signed
   - Nearing deadline
5. Add optimized pagination (cursor-based)
6. Implement location search (state/city)
7. Create API endpoint for autocomplete

**Files to Modify:**
- `apps/petitions/models.py` - add SearchVectorField
- `apps/petitions/views.py` - implement advanced filters
- `apps/petitions/forms.py` - create SearchFilterForm
- `templates/petitions/list.html` - filter UI
- `config/settings/base.py` - configure PostgreSQL search

---

### Step 16: Static File Management (S3 + CloudFront)
**Priority:** Medium  
**Estimated Time:** 4-6 hours

**Objectives:**
- Upload files to Amazon S3
- Serve files via CloudFront CDN
- Optimize media performance
- Implement retention policies

**Tasks:**
1. Configure S3 bucket with proper permissions
2. Configure CloudFront distribution
3. Install django-storages and boto3
4. Configure STATICFILES_STORAGE and DEFAULT_FILE_STORAGE
5. Implement signed URLs for private PDFs
6. Configure lifecycle policies (delete PDFs after 90 days)
7. Implement appropriate cache headers
8. Test upload/download in production

**Files to Modify:**
- `config/settings/production.py` - configure S3
- `requirements/production.txt` - add boto3, django-storages
- `apps/signatures/models.py` - adjust upload_to paths
- `apps/petitions/pdf_generator.py` - direct upload to S3

---

### Step 17: SEO Optimization
**Priority:** Medium  
**Estimated Time:** 4-5 hours

**Objectives:**
- Dynamic meta tags per page
- Open Graph for social media
- Automatic XML sitemap
- Optimized robots.txt

**Tasks:**
1. Create dynamic meta tag templates:
   - og:title, og:description, og:image for each petition
   - Twitter Cards
2. Implement structured data (JSON-LD):
   - Petition schema
   - Organization schema
3. Generate dynamic sitemap.xml
4. Configure robots.txt for production
5. Implement canonical URLs
6. Add breadcrumbs
7. Optimize titles and descriptions for SEO

**Files to Create:**
- `templates/partials/meta_tags.html` - reusable meta tags
- `apps/core/sitemaps.py` - sitemap configuration

**Files to Modify:**
- `templates/base.html` - include meta tags
- `config/urls.py` - add sitemap
- `apps/petitions/models.py` - add get_meta_description()

---

### Step 18: TailwindCSS Compilation
**Priority:** Low-Medium  
**Estimated Time:** 3-4 hours

**Objectives:**
- Configure Tailwind build pipeline
- Purge unused CSS
- Minification for production
- Hot reload in development

**Tasks:**
1. Install Tailwind CLI and dependencies
2. Create tailwind.config.js with template paths
3. Configure PostCSS
4. Create build scripts (dev and production)
5. Configure purge to remove unused CSS
6. Integrate with collectstatic
7. Add custom font (if needed)
8. Optimize bundle size (< 50KB gzipped)

**Files to Create:**
- `tailwind.config.js` - Tailwind configuration
- `postcss.config.js` - PostCSS configuration
- `package.json` - npm scripts
- `static/src/input.css` - Tailwind source file

**Files to Modify:**
- `templates/base.html` - include compiled CSS
- `Procfile` - add release command for build

---

### Step 19: Unit and Integration Testing
**Priority:** High  
**Estimated Time:** 12-16 hours

**Objectives:**
- Code coverage > 80%
- Unit tests for models, forms, validators
- Integration tests for complete workflows
- Performance tests

**Tasks:**
1. Configure pytest and pytest-django
2. Create fixtures for test data
3. Model tests:
   - Petition (validations, methods)
   - Signature (validations, status transitions)
4. Form tests:
   - SignatureSubmissionForm (CPF, validations)
   - PetitionForm (sanitization)
5. View tests:
   - Petition CRUD
   - Signature submission
   - Authentication
6. Task tests:
   - PDF verification
   - PDF generation
7. Certificate verification tests:
   - PKCS#7 parsing
   - Chain validation
   - Content verification
8. Security tests:
   - XSS prevention
   - SQL injection prevention
   - File upload validation
9. Performance tests:
   - Query optimization (< 50 queries per page)
   - Response time (< 500ms)
10. Configure CI/CD with GitHub Actions

**Files to Create:**
- `tests/` - test structure
- `tests/fixtures/` - test PDFs, certificates
- `tests/test_models.py`
- `tests/test_views.py`
- `tests/test_forms.py`
- `tests/test_tasks.py`
- `tests/test_security.py`
- `.github/workflows/tests.yml` - CI pipeline

---

### Step 20: Production Security Hardening
**Priority:** Critical  
**Estimated Time:** 6-8 hours

**Objectives:**
- Django security settings
- Mandatory HTTPS
- Protection against common attacks
- Security audit

**Tasks:**
1. Configure mandatory HTTPS:
   - SECURE_SSL_REDIRECT = True
   - SESSION_COOKIE_SECURE = True
   - CSRF_COOKIE_SECURE = True
2. Implement HSTS (HTTP Strict Transport Security)
3. Configure restrictive CSP (Content Security Policy)
4. Enable CSRF protection on all forms
5. Implement global rate limiting (django-ratelimit)
6. Configure ALLOWED_HOSTS correctly
7. Disable DEBUG in production
8. Implement security logging:
   - Failed login attempts
   - Suspicious uploads
   - CSRF violations
9. Configure SECRET_KEY via environment variable
10. Implement automatic database backup
11. Add security headers:
    - X-Content-Type-Options
    - X-Frame-Options
    - Referrer-Policy
    - Permissions-Policy
12. Run Django's check --deploy
13. Run safety check (dependency vulnerabilities)

**Files to Modify:**
- `config/settings/production.py` - complete hardening
- `config/middleware.py` - add security middleware
- `.env.example` - document required variables

---

### Step 21: Heroku Deployment Configuration
**Priority:** High  
**Estimated Time:** 6-8 hours

**Objectives:**
- Configure application for Heroku
- Configure addons (Postgres, Redis, S3)
- CI/CD pipeline
- Monitoring and logs

**Tasks:**
1. Create Procfile with web, worker and beat
2. Create runtime.txt (Python 3.13)
3. Configure buildpacks (Python + Node for Tailwind)
4. Add addons:
   - Heroku Postgres (Standard 0)
   - Heroku Redis (Premium 0)
   - Heroku Scheduler (for periodic tasks)
   - Papertrail (centralized logs)
   - New Relic or Scout APM (monitoring)
5. Configure environment variables on Heroku
6. Implement release phase for migrations
7. Configure scaling:
   - Web dynos: 2x standard-1x
   - Worker dynos: 1x standard-1x
8. Configure custom domain
9. Configure automatic SSL (Heroku ACM)
10. Implement health check endpoint
11. Configure automatic Postgres backup
12. Document deployment process

**Files to Create:**
- `Procfile` - Heroku processes
- `runtime.txt` - Python version
- `app.json` - Heroku configuration
- `DEPLOY.md` - deployment documentation

**Files to Modify:**
- `config/settings/production.py` - configure for Heroku
- `requirements/production.txt` - add gunicorn, psycopg2-binary

---

### Step 22: Production Deployment and Verification
**Priority:** Critical  
**Estimated Time:** 4-6 hours

**Objectives:**
- Initial production deployment
- Verify all components
- End-to-end testing in production
- Final documentation

**Tasks:**
1. Initial deployment via Git push
2. Run migrations in production
3. Create admin superuser
4. Load categories via fixture
5. Verify functionality:
   - Petition creation
   - PDF generation
   - Signed PDF upload
   - PKCS#7 signature verification
   - Email sending
   - Celery workers processing
6. Configure monitoring:
   - Uptime monitoring (UptimeRobot)
   - Error tracking (Sentry)
   - Performance monitoring (New Relic)
7. Configure alerts:
   - Downtime > 1 minute
   - Error rate > 1%
   - Queue depth > 100
8. Load testing:
   - 100 concurrent users
   - 1000 signatures/hour
9. Final documentation:
   - Complete README
   - Contribution guide
   - API documentation (if any)
   - Operations manual

**Final Checklist:**
- [ ] Application accessible via HTTPS
- [ ] Valid SSL certificate
- [ ] Login/registration working
- [ ] Petition creation OK
- [ ] PDF generated correctly
- [ ] Digital signature verified (PKCS#7)
- [ ] Emails being sent
- [ ] Celery workers running
- [ ] Centralized logs working
- [ ] Monitoring active
- [ ] Automatic backup configured
- [ ] DNS configured
- [ ] robots.txt and sitemap.xml accessible
- [ ] Performance < 500ms (p95)
- [ ] No 500 errors in last 24h

---

## 📊 Priority Summary

### Sprint 1 (Weeks 1-2): Production MVP
1. **Step 11:** Turnstile CAPTCHA (anti-bot protection)
2. **Step 12:** Celery in production (async processing)
3. **Step 13:** Email system (notifications)
4. **Step 21:** Heroku configuration
5. **Step 22:** Initial deployment

### Sprint 2 (Weeks 3-4): Quality and Security
6. **Step 19:** Testing (coverage > 80%)
7. **Step 20:** Security hardening
8. **Step 14:** Admin/moderation

### Sprint 3 (Weeks 5-6): Optimization and UX
9. **Step 15:** Advanced search
10. **Step 16:** S3 + CloudFront
11. **Step 17:** SEO
12. **Step 18:** Optimized TailwindCSS

---

## 🛠️ Technologies to Add

### Production
- **SendGrid/Amazon SES** - transactional email delivery
- **Amazon S3** - file storage
- **CloudFront** - CDN for static assets
- **Redis** - Celery broker and cache
- **PostgreSQL** - database (already configured)
- **Cloudflare Turnstile** - CAPTCHA

### Development
- **pytest** - testing framework
- **pytest-django** - Django integration
- **pytest-cov** - code coverage
- **factory-boy** - test fixtures
- **Faker** - fake data for tests

### Monitoring/DevOps
- **Sentry** - error tracking
- **New Relic/Scout APM** - APM
- **Papertrail** - log aggregation
- **UptimeRobot** - uptime monitoring

---

## 💰 Monthly Cost Estimate (USD)

### Heroku
- **Web Dyno (2x Standard-1x):** $50
- **Worker Dyno (1x Standard-1x):** $25
- **Postgres (Standard 0):** $50
- **Redis (Premium 0):** $15
- **Total Heroku:** ~$140/month

### AWS
- **S3 (10GB):** $0.25
- **CloudFront (100GB transfer):** $8.50
- **SES (10k emails):** $1
- **Total AWS:** ~$10/month

### Services
- **SendGrid (Essentials 50k emails):** $20
- **Cloudflare (Free Tier):** $0
- **Sentry (Developer 50k events):** $26
- **Total Services:** ~$46/month

**Total Estimated:** ~$196/month

### Cost Reduction Options
- Use Heroku Hobby dynos for development: $14/month
- PostgreSQL Mini: $5/month
- Redis Mini: $3/month
- **Minimum MVP:** ~$30/month

---

## 📚 Documentation to Create

1. **README.md** - project overview
2. **CONTRIBUTING.md** - contribution guide
3. **DEPLOY.md** - deployment process
4. **ARCHITECTURE.md** - technical architecture
5. **API.md** - API documentation (if any)
6. **SECURITY.md** - security policies
7. **CHANGELOG.md** - version history

---

## 🎯 Success KPIs

### Technical
- Uptime > 99.5%
- Response time p95 < 500ms
- Error rate < 0.1%
- Test coverage > 80%
- Lighthouse score > 90

### Business
- Average verification time < 5 minutes
- Signature approval rate > 95%
- Technical rejection rate < 2%
- NPS (Net Promoter Score) > 50

---

**Last Updated:** 01/21/2026  
**Next Review:** After Step 11 completion
