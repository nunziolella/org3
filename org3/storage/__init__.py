"""Org3 Storage Package: Multi-Cloud Adapters, 10 Persistent Domains, Anti-Quota Caching Shield."""

from org3.storage.base import (
    CANONICAL_DOMAINS,
    BaseStorageAdapter,
    DomainFolderMap,
    StorageItem,
    normalize_domain_key,
)
from org3.storage.cache import StorageCacheEngine
from org3.storage.factory import StorageAdapterFactory
from org3.storage.gdrive import GoogleDriveStorageAdapter
from org3.storage.local import LocalStorageAdapter
from org3.storage.s3 import S3StorageAdapter

__all__ = [
    "CANONICAL_DOMAINS",
    "BaseStorageAdapter",
    "DomainFolderMap",
    "StorageItem",
    "normalize_domain_key",
    "StorageCacheEngine",
    "StorageAdapterFactory",
    "GoogleDriveStorageAdapter",
    "LocalStorageAdapter",
    "S3StorageAdapter",
]
