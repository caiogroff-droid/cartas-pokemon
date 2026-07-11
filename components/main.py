from helper_functions import addCardstoDatabase, filter_to, load_cards, reset_filter

from database import init_database, toggleOwned
from variables import cartas, lastSearch

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dataclasses import dataclass
from models import Cards, Variant

# Caminhos absolutos baseados na localização deste arquivo, para que a
# aplicação funcione independentemente do diretório de onde o uvicorn
# for iniciado (não dependemos mais de estar rodando de dentro de components/).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "..", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "..", "templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(
    directory=TEMPLATES_DIR
)

init_database()


# -----------------------------------------------

@app.get("/")
def home(request: Request):
    load_cards()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "cartas": cartas,
            "tableScreen": True
        }
    )

@app.get("/search")
def search(
    request: Request,
    search: str = "",
):
    load_cards()
    cartas_filtradas = {
        link: card
        for link, card in cartas.items()
        if search.lower() in card.name.lower()
    }
    cartas.clear()
    cartas.update(cartas_filtradas)
    global lastSearch
    lastSearch = search
    return templates.TemplateResponse(
        request=request,
        name="partials/card_table.html",
        context={
            "cartas": cartas
        }
    )

@app.post("/toggle_favorite")
def toggle_favorite(
    request: Request,
    link: str = Form(...),
    variant_name: str = Form(...),
):
    toggleOwned(link, variant_name)

    return templates.TemplateResponse(
        request=request,
        name="partials/variant_row.html",
        context={
            "variant": next(variant for variant in cartas[link].variants if variant.name == variant_name),
            "link": link,
            "card": cartas[link]
        }
    )


@app.get("/reset")
def reset(request: Request):
    reset_filter()
    return home(request)

@app.post("/change-filter")
def change_filter(request: Request, owned: str | None = Form(None)):
    filter_to(owned)
    return search(request, lastSearch)


@app.get("/add-card")
def add_card_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add_card_form.html",
        context={
            "tableScreen": False
        }
    )

@app.post("/add-card")
def add_card_confirm(
    request: Request,
    links: str = Form(...)
):
    lista_links = [
        l.strip()
        for l in links.splitlines()
        if l.strip()
    ]

    try:
        addCardstoDatabase(lista_links)
    except Exception as e:
        print(f"failed to add card to database due to: ", e)
    finally:
        load_cards()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "cartas": cartas,
                "tableScreen": True
            }
        )