# Migration System

The Lambda Heat Pumps integration includes a migration system to handle version upgrades and breaking changes.

## Overview

The migration system ensures:

- Smooth upgrades between versions
- Preservation of entity configurations
- Handling of breaking changes
- Backward compatibility

## Migration Process

### 1. Version Detection

On startup, the integration checks:

- Current integration version
- Stored configuration version
- Entity registry state

### 2. Migration Execution

If a migration is needed:

- Migration functions are called in order
- Configuration is updated
- Entity registry is migrated
- Data is preserved

### 3. Validation

After migration:

- Configuration is validated
- Entities are verified
- Errors are logged

## Migration Functions

### Configuration Migration

Update configuration format:

```python
async def migrate_config(version: str, config: dict) -> dict:
    # Update configuration structure
    return updated_config
```

### Entity Registry Migration

Update entity registry entries:

```python
async def migrate_entities(version: str, entities: list) -> list:
    # Update entity unique IDs
    return updated_entities
```

## Version Management

### Version Numbers

Follow semantic versioning:

- **Major**: Breaking changes
- **Minor**: New features
- **Patch**: Bug fixes

### Migration Mapping

Map versions to migration functions:

```python
MIGRATIONS = {
    "2.0.0": migrate_to_2_0_0,
    "2.0.1": migrate_to_2_0_1,
}
```

## Breaking Changes

### Entity ID Changes

When entity IDs change:

- Old entities are removed
- New entities are created
- User is notified

### Configuration Changes

When configuration format changes:

- Old format is converted
- New format is validated
- Defaults are applied

## Best Practices

- Always test migrations
- Provide clear migration messages
- Preserve user data
- Document breaking changes

## Related Documentation

- [Architecture](architecture.md)
- [Contributing Guide](contributing.md)

