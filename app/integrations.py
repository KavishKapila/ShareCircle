"""Local no-op integration hooks for future sponsor services."""

def send_sms(phone, body):
    """Sponsor hook for an SMS provider; safe no-op by default."""
    _ = (phone, body)
    # Sponsor hook: connect Twilio here when a key-backed integration is desired.
    return None


def send_email(to, subject, body):
    """Sponsor hook for an email provider; safe no-op by default."""
    _ = (to, subject, body)
    # Sponsor hook: connect SendGrid here when a key-backed integration is desired.
    return None


def geocode(address):
    """Sponsor hook for address-to-coordinate lookup."""
    _ = address
    # Sponsor hook: connect Mapbox here when external geocoding is desired.
    return None


def process_donation(amount, currency):
    """Sponsor hook for a donation/payment provider; safe no-op by default."""
    _ = (amount, currency)
    # Sponsor hook: connect Stripe here when a donation workflow is desired.
    return None
