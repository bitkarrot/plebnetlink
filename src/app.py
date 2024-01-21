import http
import httpx
# import asyncio
import os
from typing import Union

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from .exchange_rates import fiat_amount_as_satoshis
from .utils import get_lnbits_satspay, is_https_url

discord_var = os.environ.get('DISCORD_VAR')

TITLE = "satspay session"
APP_DESC = "simple url bridge to lnbits satspay extension"

app = FastAPI(
    title=TITLE,
    description=APP_DESC,
    version="0.0.1 alpha",
    contact={
        "name": "bitkarrot",
        "url": "http://github.com/bitkarrot",
    },
    license_info={
        "name": "MIT License",
        "url": "https://mit-license.org/",
    },
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")


async def handle_params(*args):
    """
    Handle the parameters passed to the function.

    Args:
        *args: Variable length argument list.

    Returns:
        str: The response URL if the parameters are valid and the
                function is able to generate a response URL.
            If the number of arguments is 2, the response URL is generated
                using the `amount` and `description` arguments.
            If the number of arguments is 3, the response URL is generated
                using the `sats`, `description`, and `fiat` arguments.
            If the number of arguments is neither 2 nor 3, an error message is returned.

    Raises:
        None
    """
    logger.info(args)

    if len(args) == 2:
        amount, description = args
        res_url = await get_lnbits_satspay(int(amount), description)
        logger.info(f"2 args, handle params response: {res_url}")
        return res_url
    elif len(args) == 3:
        fiat, amount, description = args
        if isinstance(amount, int):
            logger.info(f"fiat: {fiat.upper()} amt: {int(amount)} description: {description}")
            sats =  await fiat_amount_as_satoshis(int(amount), fiat.upper())
            logger.info(f"fiat amt in satoshis: {sats}")
            res_url = await get_lnbits_satspay(sats, description)
            logger.info(f"3 args, handle params response: {res_url}")
            return res_url
    else:
        return f"Endpoint for {fiat}, No amount provided as integer."


@app.get("/fiat/{fiat}/amt/{amount}")
async def dynamic_endpoint(fiat: str, amount: int):
    """
    An asynchronous function that handles a dynamic endpoint.

    Parameters:
    - fiat (str): The fiat currency.
    - amount (int): The amount.

    Returns:
    - The URL to redirect to if it is an HTTPS URL.
    - Otherwise, the URL itself.
    """
    res_url = await handle_params(fiat, amount, "")
    if is_https_url(res_url):
        return RedirectResponse(url=res_url, status_code=302)
    else:
        return res_url


@app.get("/fiat/{fiat}/amt/{amount}/desc/{description}")
async def dynamic_longendpoint(fiat: str, amount: int, description: str):
    """
    A function that handles a dynamic long endpoint.

    Parameters:
        fiat (str): The fiat currency.
        amount (int): The amount.
        description (str): The description.

    Returns:
        Union[RedirectResponse, str]: The result URL or a RedirectResponse if the URL is HTTPS.
    """
    res_url = await handle_params(fiat, amount, description)
    if is_https_url(res_url):
        return RedirectResponse(url=res_url, status_code=302)
    else:
        return res_url


@app.get("/amt/{amount}/desc/{description}")
async def dynamic_satendpoint(amount: int, description: str):
    """
    Endpoint for satoshis amount and description
    """
    res_url = await handle_params(amount, description)
    if is_https_url(res_url):
        return RedirectResponse(url=res_url, status_code=302)
    else:
        return res_url

@app.get("/amount/{amount}")
async def dynamic_sats(amount: int, desc: Union[str, None] = None):
    """
    returns a text link only
    /amount/{amount}?desc={desc}
    ## get tx id from the res_url
    ## e.g.  https://testnet.plebnet.dev/satspay/MnzCtpphVdrDgXzVtiNWTb
    ## so we can check the tx id in lnbits for completion 
    """
    logger.info(f"amt: {amount} desc: {desc}")
    description = ""
    if not isinstance(desc, type(None)):
        description = desc
    logger.info(f'description: {description}')
    res_url = await handle_params(amount, description)
    return res_url


@app.get("/fee/{amount}")
async def register_sats(amount: int, desc: Union[str, None] = None):
    """
    Endpoint for satoshis amount only
    with option for desc in the url, e.g.
    /fee/{amount}?desc={desc}
    """
    #logger.info(f"fee: {amount} desc: {desc}")
    description = ""
    if not isinstance(desc, type(None)):
        description = desc
    #logger.info(f'description: {description}')
    res_url = await handle_params(amount, description)
    if is_https_url(res_url):
        return RedirectResponse(url=res_url, status_code=302)
    else:
        return res_url


@app.get("/")
async def initial_page(request: Request):
    """
    This function is the handler for the initial page of the application.

    Parameters:
        - request (Request): The request object containing information about the HTTP request.

    Returns:
        - TemplateResponse: The response containing the rendered "index.html" template.
    """
    fiat = "USD"
    description = "Meeting"
    return templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            "title": "SatsPay Link",
            "fiat": fiat,
            "description": description,
            "amount": 100,
        },
    )

@app.get("/thanks")
async def thanks_page(request: Request):
    """
    Get the thanks page.

    Args:
        request (Request): The incoming request object.

    Returns:
        TemplateResponse: The rendered thanks.html template.
    """
    logger.info("Inside GET /thanks endpoint")
    query_params = request.query_params
    if query_params:
        logger.info("thanks endpoint, data via GET")
        for param_name, param_value in query_params.items():
            print(f"Parameter Name: {param_name}, Value: {param_value}")
    else:
        logger.info("No data received via GET")
    return templates.TemplateResponse("thanks.html", context={"request": request})


async def get_insert_data(data):
    extracted_data = {
    'id': data['record']['id'],
    'name': data['record']['name'],
    'goal': data['record']['goal'],
    'email': data['record']['email'],
    'github': data['record']['github'],
    'mentor': data['record']['mentor'],
    'twitter': data['record']['twitter'],
    'datetime': data['record']['datetime'],
    'experience': data['record']['experience'],
    'payment_id': data['record']['payment_id'],
    'discord_username': data['record']['discord_username'],
    'payment_status': data['record']['payment_status']
    }
    # Pretty print the extracted data
    pretty_data = ''
    for key, value in extracted_data.items():
        pretty_data += f'**{key}**: {value}' + '\n'

    return pretty_data

async def send_discord_message(content):
    url = "https://discord.com/api/webhooks/1196557151456481411/" + discord_var
    payload = {"content": content}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")
        print(f"Response content: {response.text}")


# database updates
@app.post("/webhook", status_code=http.HTTPStatus.ACCEPTED)
async def webhook_post(request: Request):
    """
    A handler for the HTTP POST request to '/thanks'.

    Parameters:
        request (Request): The incoming HTTP request object.

    Returns:
        TemplateResponse: The HTML template response for 'thanks.html'.
    """
    logger.info("Inside POST /webhook endpoint") 
    # payload = await request.body()
    # logger.info(f"Thanks body POST: {str(payload)}")
    data = await request.json()
    logger.info(f"POST json DATA: {data}")

    # send data to discord webhook
    if data['type'] == 'INSERT':
        insert_data =  get_insert_data(data)
        logger.info('formatted insert_data: ' + insert_data)
        send_discord_message(insert_data)

    return templates.TemplateResponse("thanks.html", context={"request": request})


# @app.get("/paylink", status_code=http.HTTPStatus.ACCEPTED)
# async def paylink_post(request: Request):
#     query_params = request.query_params
#     logger.info("Inside GET /paylink endpoint")
#     if query_params:
#         logger.info("thanks endpoint, data via GET")
#         for param_name, param_value in query_params.items():
#             print(f"Parameter Name: {param_name}, Value: {param_value}")
#     else:
#         logger.info("No data received via GET")

# #    data = await request.json()
# #    logger.info(f'POST json from paylink endpoint: {data}')
#     return "ok"


# @app.post("/paylink", status_code=http.HTTPStatus.ACCEPTED)
# async def paylink_post(request: Request):
#     """
#         paylink POST endpoint
#     """
#     logger.info("Inside POST /paylink endpoint")
#     # payload = await request.body()
#     # logger.info(f"paylink body POST: {str(payload)}")
#     data = await request.json()
#     logger.info(f"POST json from paylink endpoint: {data}")
#     return "ok"


@app.get("/about")
def about():
    """
    Get information about the application.
    """
    return "About"

