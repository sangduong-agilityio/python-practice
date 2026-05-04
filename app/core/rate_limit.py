from slowapi import Limiter
from slowapi.util import get_remote_address

# We use the client's IP address (get_remote_address) to track their request count.
# Redis can also be used as a backend for the rate limiter,
# but in-memory is enough for this single-instance setup and satisfies the standard requirement.
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)
