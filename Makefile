.PHONY: dev prod down stop start logs shell stripe ext-dev ext-build ext-zip screenshots

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod:
	docker compose up --build

stop:
	docker compose stop

start:
	docker compose start

down:
	docker compose down

logs:
	docker compose logs -f api

shell:
	docker compose exec api bash

stripe:
	stripe listen --forward-to localhost:8000/webhook/stripe

ext-dev:
	cd extension && npm run dev

ext-build:
	cd extension && npm run build

ext-zip:
	./extension/package.zip.sh

screenshots:
	cd screenshots && npm run dev
