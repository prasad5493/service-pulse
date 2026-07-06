#!/usr/bin/env bash
#
# One-time setup: creates the storage account that holds Terraform state.
# This is the only thing not managed by Terraform itself (chicken and egg —
# Terraform needs somewhere to keep its state before it can create anything).
#
# Usage: ./scripts/bootstrap.sh <subscription-id> [location]

set -euo pipefail

SUBSCRIPTION_ID="${1:?Usage: ./scripts/bootstrap.sh <subscription-id> [location]}"
LOCATION="${2:-uksouth}"

RESOURCE_GROUP="rg-tfstate"
STORAGE_ACCOUNT="stservicepulsetfstate"
CONTAINER="tfstate"

echo "==> Using subscription $SUBSCRIPTION_ID"
az account set --subscription "$SUBSCRIPTION_ID"

echo "==> Creating resource group $RESOURCE_GROUP in $LOCATION"
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

echo "==> Creating storage account $STORAGE_ACCOUNT"
az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --output none

echo "==> Creating blob container $CONTAINER"
az storage container create \
  --name "$CONTAINER" \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login \
  --output none

echo ""
echo "Done. Terraform state will live in:"
echo "  $STORAGE_ACCOUNT/$CONTAINER/service-pulse.tfstate"
