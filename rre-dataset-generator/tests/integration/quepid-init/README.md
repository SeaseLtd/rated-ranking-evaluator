# Quepid

Guide: https://quepid-docs.dev.o19s.com/2/quepid/61/how-to-deploy-quepid-locally

**Note:** Eric proposed the nightly version, which it's a lot simpler and easier to configure. 


## Configuration and checks

- A single environment file `tests/integration/quepid-init/corenv` is passed to both services (`app` and `mysql`).
- Compose does NOT interpolate `${VARS}` from an `env_file`, so the `app` service avoids `${...}` in `environment` and relies on `corenv`.
- The MySQL healthcheck escapes `$` as `$$MYSQL_ROOT_PASSWORD` so the variable expands inside the container, not by Compose.

### Environment variables (corenv)

Current `corenv` used by this compose:

```env
MYSQL_ROOT_PASSWORD=change_me                           # mysql: required (initial root password), also used by healthcheck
MYSQL_DATABASE=quepid                                   # mysql: required (DB to create)
DATABASE_URL=mysql2://root:change_me@mysql:3306/quepid  # app: required (DB connection string)
SECRET_KEY_BASE=<128 hex chars>                         # app: required (Rails production secret)

QUEPID_DOMAIN=http://localhost           # app: optional (base URL)
SIGNUP_ENABLED=true                      # app: optional (allow signups)
QUEPID_DEFAULT_SCORER=NDCG_CUT@10        # app: optional (default scorer)
```

What’s actually used:
- __mysql service__: `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE` (+ healthcheck reads `MYSQL_ROOT_PASSWORD`).
- __app service (Quepid)__: `DATABASE_URL`, `SECRET_KEY_BASE`, `QUEPID_DOMAIN`, `SIGNUP_ENABLED`, `QUEPID_DEFAULT_SCORER`.
- Note: `MYSQL_*` vars are present in `app` via `env_file`, but the app does not use them directly (it uses `DATABASE_URL`).



## Useful inspection commands / checks

- Show combined config (no changes applied):
```bash
docker compose -f docker-compose.quepid.yml config
```

- Check MySQL is up and DB exists:
```bash
docker compose -f docker-compose.quepid.yml exec -T mysql \
  mysql -uroot -pchange_me -e "SHOW DATABASES; SELECT VERSION() AS version, @@version_comment AS distro;"
```

- Inspect key MySQL variables:
```bash
docker compose -f docker-compose.quepid.yml exec -T mysql \
  mysql -uroot -pchange_me -e "SHOW VARIABLES WHERE Variable_name IN ('character_set_server','collation_server','sql_mode','max_connections');"
```

- Verify Quepid app environment:
```bash
docker compose -f docker-compose.quepid.yml exec -T app \
  env | egrep '^(DATABASE_URL|RAILS_ENV|RACK_ENV|QUEPID_DOMAIN|QUEPID_DEFAULT_SCORER|SIGNUP_ENABLED)='
```

- Quick HTTP check (should 302 to login):
```bash
curl -sI http://localhost | head -n 1
```
