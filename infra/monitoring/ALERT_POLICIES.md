# Alert Policies & Incident Response

**Last Updated**: October 31, 2025  
**Status**: Ready for Implementation  
**Review Frequency**: Quarterly

---

## Alert Priority Levels

### P0 - Critical (Immediate Response Required)

**Definition**: Service outage or severe degradation affecting all users.

**Response Time**: Immediate (< 15 minutes)  
**Notification**: PagerDuty + Email + Slack  
**Owner**: On-call engineer  
**Escalation**: After 30 minutes, escalate to engineering lead

### P1 - High (Urgent but Not Critical)

**Definition**: Significant impact on user experience or system functionality.

**Response Time**: Within 4 hours  
**Notification**: Email + Slack  
**Owner**: Engineering team  
**Escalation**: After 8 hours, escalate to engineering lead

### P2 - Medium (Non-Urgent)

**Definition**: Minor issues that don't significantly impact users.

**Response Time**: Within 24 hours  
**Notification**: Email  
**Owner**: Engineering team  
**Escalation**: After 48 hours, review in weekly standup

### P3 - Low (Informational)

**Definition**: Maintenance notifications, performance degradation warnings.

**Response Time**: Within 1 week  
**Notification**: Email  
**Owner**: Engineering team  
**Escalation**: None (address in sprint planning)

---

## Alert Conditions

### P0 Alerts

#### API Down

**Condition**: Health check fails for >5 minutes  
**Detection**: Railway health checks + external monitor  
**Impact**: Frontend unable to load data  
**Response**: Immediate investigation

**Automated Actions**:
- Send PagerDuty alert
- Post to #incidents Slack channel
- Create incident in status page

**Response Checklist**:
1. Check Railway service status (running/crashed)
2. Check deployment logs for errors
3. Check database connectivity
4. Check Redis connectivity
5. If deployment issue: rollback to previous version
6. If database issue: check Neon status
7. Communicate in #incidents channel every 15 minutes
8. Update status page with ETA

**Example Commands**:
```bash
# Check service status
railway status

# Check logs for errors
railway logs --tail 100

# Test database connection
railway run python -c "from app.database import engine; engine.connect()"

# Rollback deployment
railway rollback
```

---

#### Database Connection Lost

**Condition**: PostgreSQL connection errors for >2 minutes  
**Detection**: Sentry error spike + Railway logs  
**Impact**: All API requests fail  
**Response**: Immediate investigation

**Automated Actions**:
- Send PagerDuty alert
- Post to #incidents Slack channel

**Response Checklist**:
1. Check Neon database status: https://neon.tech/status
2. Check `DATABASE_URL` environment variable is set
3. Check database connection limits
4. Check for long-running queries blocking connections
5. If Neon outage: communicate ETA to users
6. If connection limit reached: restart service to clear connections
7. If query blocking: identify and kill blocking query

**Example Commands**:
```bash
# Test database connection
railway run python -c "import os; from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); print('OK' if engine.connect() else 'FAIL')"

# Check active connections (if can connect)
railway run python -c "from sqlalchemy import create_engine, text; import os; engine = create_engine(os.getenv('DATABASE_URL')); with engine.connect() as conn: print(conn.execute(text('SELECT count(*) FROM pg_stat_activity')).scalar())"
```

---

#### Error Rate >10%

**Condition**: >10% of requests returning 500 errors for >5 minutes  
**Detection**: Sentry error rate alert + Railway metrics  
**Impact**: Significant user experience degradation  
**Response**: Immediate investigation

**Automated Actions**:
- Send Email + Slack alert
- Create Sentry issue

**Response Checklist**:
1. Check Sentry dashboard for error details
2. Identify error pattern (all endpoints or specific?)
3. Check recent deployments (was new code deployed?)
4. Check database performance (slow queries?)
5. Check external API failures (OpenAI, etc.)
6. If deployment-related: rollback
7. If database-related: optimize queries or scale up
8. If external API: implement circuit breaker or retry logic

**Example Commands**:
```bash
# Check recent errors in Sentry
# Go to: https://sentry.io/organizations/[org]/projects/agi-tracker-api/

# Check recent deployments
railway deployments

# Check current error rate
railway logs --tail 100 | grep -i "error"
```

---

### P1 Alerts

#### LLM Budget Exceeded

**Condition**: Daily LLM spend >$20 (or configured limit)  
**Detection**: Redis budget tracker + Sentry warning  
**Impact**: LLM features disabled for rest of day  
**Response**: Within 4 hours

**Automated Actions**:
- Send Email + Slack alert
- Disable LLM features automatically

**Response Checklist**:
1. Check which LLM tasks consumed budget
2. Review recent LLM calls in logs
3. Check for unusual patterns (retry storms, etc.)
4. Verify budget limit is correct (`LLM_BUDGET_DAILY_USD`)
5. If legitimate usage: increase budget for tomorrow
6. If bug (retry storm): fix and redeploy
7. If malicious: block IP and report

**Example Commands**:
```bash
# Check LLM budget usage
railway run python -c "from app.utils.llm_budget import get_daily_spend; print(get_daily_spend())"

# Check recent LLM calls
railway logs --tail 500 | grep -i "llm\|openai"
```

---

#### Celery Queue >100 Items

**Condition**: Celery queue length >100 items for >30 minutes  
**Detection**: Celery monitoring + Healthchecks.io  
**Impact**: Tasks delayed, potential backlog  
**Response**: Within 4 hours

**Automated Actions**:
- Send Email alert
- Log warning in Sentry

**Response Checklist**:
1. Check Celery worker status (running/crashed)
2. Check task execution times (slow tasks?)
3. Check task failure rate (retrying indefinitely?)
4. Check Redis connection (queue backend)
5. If worker crashed: restart worker
6. If tasks slow: optimize or scale workers
7. If tasks failing: fix bug and clear failed tasks

**Example Commands**:
```bash
# Check Celery queue length
railway run celery -A app.celery_app inspect reserved

# Check active tasks
railway run celery -A app.celery_app inspect active

# Check worker status
railway run celery -A app.celery_app inspect active_queues

# Purge queue (emergency only)
railway run celery -A app.celery_app purge
```

---

#### Memory Usage >800MB Sustained

**Condition**: Memory >800MB for >15 minutes  
**Detection**: Railway metrics dashboard  
**Impact**: Risk of OOM crash  
**Response**: Within 4 hours

**Automated Actions**:
- Send Email alert

**Response Checklist**:
1. Check Railway metrics for memory trend
2. Check for memory leaks (increasing over time?)
3. Check recent deployments (new code using more memory?)
4. Check active database connections (connection pooling issue?)
5. If leak: identify and fix code, redeploy
6. If legitimate usage: scale up Railway plan
7. If temporary spike: monitor and wait

**Example Commands**:
```bash
# Check current memory usage
# Via Railway dashboard: Metrics tab

# Check process memory
railway run python -c "import psutil; import os; process = psutil.Process(os.getpid()); print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')"
```

---

### P2 Alerts

#### Slow API Responses (P95 >500ms)

**Condition**: 95th percentile response time >500ms for >10 minutes  
**Detection**: Railway metrics + Sentry performance monitoring  
**Impact**: Slower user experience  
**Response**: Within 24 hours

**Automated Actions**:
- Send Email alert

**Response Checklist**:
1. Check Railway metrics for slow endpoints
2. Check Sentry performance dashboard
3. Identify slow queries (database N+1 queries?)
4. Check external API latency (OpenAI, etc.)
5. Check cache hit rate (Redis caching working?)
6. Optimize slow queries (add indexes, reduce data)
7. Implement caching for slow endpoints
8. Scale database or Redis if needed

**Example Commands**:
```bash
# Check slow queries (if database is slow)
railway run python -c "from sqlalchemy import create_engine, text; import os; engine = create_engine(os.getenv('DATABASE_URL')); with engine.connect() as conn: result = conn.execute(text('SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10')); print([dict(r._mapping) for r in result])"

# Check cache hit rate
railway run python -c "from redis import Redis; import os; r = Redis.from_url(os.getenv('REDIS_URL')); info = r.info('stats'); print(f\"Cache hits: {info.get('keyspace_hits', 0)}, Misses: {info.get('keyspace_misses', 0)}\")"
```

---

#### Failed Healthchecks.io Ping

**Condition**: Scheduled task missed expected ping time  
**Detection**: Healthchecks.io email notification  
**Impact**: Task may not have run, data may be stale  
**Response**: Within 24 hours

**Automated Actions**:
- Send Email notification

**Response Checklist**:
1. Check Celery Beat schedule is correct
2. Check Celery worker is running
3. Check task execution logs
4. Check if task failed with error
5. Check if task timed out
6. If one-time miss: manually trigger task
7. If recurring: fix task or adjust schedule
8. Update Healthchecks.io grace period if needed

**Example Commands**:
```bash
# Check Celery Beat status
railway run celery -A app.celery_app inspect active

# Manually trigger task
railway run celery -A app.celery_app call fetch_all_feeds

# Check task logs
railway logs --tail 500 | grep -i "fetch_all_feeds"
```

---

## Alert Channels

### Email

**Recipients**:
- Engineering team mailing list
- On-call engineer (P0/P1 only)

**Configuration**:
- Sentry: Settings → Alerts → Email
- Healthchecks.io: Integrations → Email
- Railway: Settings → Notifications

### Slack

**Channel**: `#agi-tracker-alerts`

**Configuration**:
- Sentry: Settings → Integrations → Slack
- Railway: Settings → Integrations → Slack

**Alert Format**:
```
🚨 P0: API Down
Service: agitracker-production-6efa
Duration: 5 minutes
Impact: All users unable to access app
Action: Investigating...
```

### PagerDuty (Optional)

**Status**: Not yet configured

**Setup**:
1. Create PagerDuty account
2. Create service: "AGI Tracker API"
3. Get integration key
4. Configure Sentry integration
5. Configure Railway integration (if available)
6. Set up on-call schedule

---

## Incident Response Workflow

### Step 1: Detection

Alert received via email/Slack/PagerDuty

### Step 2: Acknowledgment

**P0**: Acknowledge within 15 minutes  
**P1**: Acknowledge within 1 hour  
**P2**: Acknowledge within 4 hours

**How to acknowledge**:
- Reply in Slack thread: "Investigating"
- Update PagerDuty incident status
- Post in #incidents channel (P0 only)

### Step 3: Investigation

Follow response checklist for specific alert type (see above).

**Best practices**:
- Document steps taken in Slack thread
- Share findings as you discover them
- Ask for help if stuck after 30 minutes (P0) or 2 hours (P1)

### Step 4: Mitigation

Implement fix:
- Code fix → Deploy to production
- Configuration fix → Update Railway environment variables
- Infrastructure fix → Scale resources or restart services

**Deployment checklist**:
- [ ] Fix tested locally (if possible)
- [ ] Fix reviewed by peer (P0/P1)
- [ ] Deployment plan documented
- [ ] Rollback plan ready
- [ ] Team notified before deploy
- [ ] Deployment monitored (stay online for 15 minutes)

### Step 5: Verification

Confirm alert resolved:
- [ ] Alert condition cleared (metrics back to normal)
- [ ] Test user flow working
- [ ] Monitor for 30 minutes (P0) or 1 hour (P1/P2)
- [ ] No new related alerts

### Step 6: Communication

**During incident** (P0 only):
- Update #incidents channel every 15 minutes
- Update status page if user-facing
- Post final resolution message

**After resolution**:
- Close incident in PagerDuty
- Mark Slack thread as resolved
- Thank team members who helped

### Step 7: Post-Mortem

**Required for**: P0 and P1 incidents  
**Timeline**: Within 1 week of resolution  
**Template**: See POST_MORTEM_TEMPLATE.md

**Post-mortem agenda**:
1. What happened? (timeline)
2. What was the impact? (users affected, duration)
3. What was the root cause?
4. How was it detected?
5. How was it resolved?
6. What can we do better? (action items)

---

## On-Call Schedule

**Status**: Not yet configured

**Proposed Schedule**:
- Weekly rotation (Monday-Monday)
- 24/7 coverage for P0 alerts
- Business hours coverage for P1 alerts
- On-call engineer has laptop and phone access
- Backup engineer designated each week

**Responsibilities**:
- Respond to P0 alerts within 15 minutes
- Respond to P1 alerts within 1 hour
- Escalate if unable to resolve within SLA
- Document all incidents in #incidents channel
- Write post-mortems for P0/P1 incidents

---

## Escalation Matrix

### L1: On-Call Engineer

**Handles**: All P0/P1 alerts  
**Escalates to L2 after**: 30 minutes (P0) or 4 hours (P1)

### L2: Engineering Lead

**Handles**: Complex incidents requiring architectural decisions  
**Escalates to L3 after**: 2 hours (P0) or 1 day (P1)

### L3: CTO/Technical Founder

**Handles**: Major incidents requiring executive decisions (e.g., service migration, major downtime)

---

## Alert Fatigue Prevention

### Best Practices

1. **Tune Alert Thresholds**:
   - Review alert frequency monthly
   - Adjust thresholds if >10 false positives/week
   - Remove alerts with <1 actionable incident/month

2. **Use Severity Correctly**:
   - Don't over-use P0 (reserve for true outages)
   - Use P2/P3 for warnings and informational alerts

3. **Batch Non-Critical Alerts**:
   - Send P2 alerts as daily digest
   - Send P3 alerts as weekly digest

4. **Auto-Resolve Where Possible**:
   - Use Sentry auto-resolve for resolved issues
   - Use Healthchecks.io grace periods to avoid transient failures

5. **Silence During Maintenance**:
   - Disable alerts during planned maintenance
   - Re-enable immediately after maintenance complete

---

## Testing Alert System

### Monthly Alert Test

**Schedule**: First Monday of each month

**Procedure**:
1. Trigger test Sentry error
2. Trigger test Healthchecks.io failure
3. Verify emails received
4. Verify Slack notifications received
5. Verify PagerDuty notifications received (if configured)
6. Document any issues

**Test Commands**:
```bash
# Test Sentry
railway run python -c "import sentry_sdk; sentry_sdk.capture_message('Monthly alert test', level='error')"

# Test Healthchecks.io
curl https://hc-ping.com/[uuid]/fail
```

---

## Metrics to Track

### Alert Metrics

- Total alerts per week (by priority)
- False positive rate (alerts that required no action)
- Mean time to acknowledge (MTTA)
- Mean time to resolve (MTTR)
- Escalation rate (% of incidents escalated)

### Incident Metrics

- Total incidents per month (by priority)
- Incident duration (mean, median, p95)
- User impact (users affected, duration)
- Repeat incidents (same root cause >1 time)

### Review Frequency

- Weekly: Review P0 incidents
- Monthly: Review all incidents and alert metrics
- Quarterly: Review alert policies and update thresholds

---

## Resources

- **Sentry Alert Configuration**: https://docs.sentry.io/product/alerts/
- **Healthchecks.io Integration**: https://healthchecks.io/docs/
- **Railway Monitoring**: https://docs.railway.app/reference/monitoring
- **Incident Response Best Practices**: https://response.pagerduty.com/

---

**Status**: Ready for Implementation  
**Next Action**: Configure alert channels and test alert system  
**Review Date**: February 1, 2026 (quarterly review)

