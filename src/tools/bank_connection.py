import os
import plaid
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)

client_id = os.environ.get("PLAID_CLIENT_ID") or "654fe157dd1446001b7ea45f"
secret = os.environ.get("PLAID_SECRET") or "7a8bcc9f552b884bc803c433beb320"
# Available environments are
# 'Production'
# 'Development'
# 'Sandbox'
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        "clientId": client_id,
        "secret": secret,
    },
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Create a public token
response = client.sandbox_public_token_create(
    plaid.SandboxPublicTokenCreateRequest(
        institution_id="ins_3",
        initial_products=["transactions"],
    )
)
