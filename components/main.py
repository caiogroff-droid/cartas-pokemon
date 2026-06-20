from helper_functions import addCardstoDatabase, load_cards

from database import init_database, get_conn, toggleOwned
from variables import *

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


# init app ----------------------------------

app = FastAPI()
app.mount("/static", StaticFiles(directory="../static"), name="static")

templates = Jinja2Templates(
    directory="../templates"
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
    global currentfilterType
    currentfilterType = FilterType.ALL
    return home(request)

@app.post("/change-filter")
def change_filter(request: Request, owned: str | None = Form(None)):
    print(owned)
    global currentfilterType
    match owned:
        case 'on':
            currentfilterType = FilterType.OWNED
        case None:
            currentfilterType = FilterType.ALL
    return search(request, lastSearch)


@app.get("/add-card")
def add_card_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add_card_form.html",
        context={
            "loading": loading,
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