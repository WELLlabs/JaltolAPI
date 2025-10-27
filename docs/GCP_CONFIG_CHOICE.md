# GCP Compute Service Comparison

## Cloud Run (Containers) - RECOMMENDED

**How it works:**
- Container shuts down after ~15 min of inactivity (scales to zero)
- Cold start delay: 3-5 seconds when resuming from idle state
- Auto-scales to handle traffic spikes (default max: 100 containers)
- Best for: Intermittent traffic, cost-conscious deployments

**Cost components:** Requests ($0.40/million) + compute time ($0.12 per 10K requests) + network egress ($0.12/GB)

**Example costs (10K requests/month, 500 KB responses):**
- Requests: $0.004
- Compute: $0.12
- Egress (4 GB): $0.48
- **Total: $0.60/month** ✓

**CI/CD:** Simplest - GitHub push triggers Cloud Build → auto-deploy (~2-3 min)

---

## App Engine Standard (Instances)

**How it works:**
- Keeps 1+ instances warm during active hours (no cold starts)
- Auto-detects traffic patterns, scales down during off-hours
- Best for: Consistent traffic, predictable performance needs

**Cost components:** Instance hours (~$0.05/hour) + network egress ($0.12/GB)

**Example costs (240 instance-hours/month, 4 GB egress):**
- Instances: $10.60
- Egress: $0.48
- **Total: $11/month** ✓

**CI/CD:** Good integration with Cloud Build, slower deployments (~5-8 min)

---

## Compute Engine (VMs)

**How it works:**
- VM runs 24/7 (always-on, no scaling-to-zero)
- Must manually configure auto-scaling, load balancing, health checks
- Best for: Full control, legacy migrations, complex networking

**Cost components:** VM runtime (~$7/month for e2-micro) + network egress ($0.12/GB) + setup/maintenance time

**Example costs (24/7 uptime, 4 GB egress):**
- VM: $7.11
- Egress: $0.48
- **Total: $7.60/month** + management overhead

**CI/CD:** Most complex - requires SSH keys, deployment scripts, custom automation

---

## Key Insights

**Network egress costs are identical** across all services ($0.12/GB after 1 GB free)

**Cloud Run wins at low-medium traffic** (<100K requests/month) due to zero-cost idle time

**App Engine/Compute Engine win only at very high traffic** (>500K requests/month) where fixed costs amortize

**Recommended:** Start with Cloud Run (scale to zero), add min-instances ($0→$10/month) if cold starts become problematic