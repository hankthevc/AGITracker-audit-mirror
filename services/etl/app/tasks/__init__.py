"""ETL tasks module."""

# Import all tasks to register them with Celery
from app.tasks.extract_claims import *  # noqa: F401, F403
from app.tasks.fetch_feeds import *  # noqa: F401, F403
from app.tasks.fetch_gpqa import *  # noqa: F401, F403
from app.tasks.fetch_hle import *  # noqa: F401, F403
from app.tasks.fetch_osworld import *  # noqa: F401, F403
from app.tasks.fetch_swebench import *  # noqa: F401, F403
from app.tasks.fetch_webarena import *  # noqa: F401, F403
from app.tasks.healthchecks import *  # noqa: F401, F403
from app.tasks.link_entities import *  # noqa: F401, F403
from app.tasks.llm_budget import *  # noqa: F401, F403
from app.tasks.security_maturity import *  # noqa: F401, F403
from app.tasks.seed_inputs import *  # noqa: F401, F403
from app.tasks.snap_index import *  # noqa: F401, F403
