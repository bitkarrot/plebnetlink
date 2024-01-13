from loguru import logger
from .exchange_rates import fiat_amount_as_satoshis

import os
import json
import requests
# import asyncio

INVOICE_API_KEY = os.environ["INVOICE_API_KEY"]
LNBITS_WALLET = os.environ["LNBITS_WALLET"]
ONCHAIN_WALLET = os.environ["ONCHAIN_WALLET"]
LNBITS_URL = os.environ["LNBITS_URL"]
webhook = os.environ["WEBHOOK"]
completelink = os.environ["COMPLETELINK"]
completelinktext = os.environ["COMPLETELINKTEXT"]
customcss = os.environ["CUSTOMCSS"]

sats_url = "/satspay/api/v1/charge"
email_url = "/smtp/api/v1/email/"

# TODO: integrate webhook data forwarded

async def get_lnbits_satspay(sats_amount: int, desc: str):
    url = LNBITS_URL + sats_url
    default_desc = "LNBits Invoice"
    logger.info("Default description: ", default_desc)

    if desc == "":
        desc = default_desc

    logger.info("description: ", desc)

    body = {
        "onchainwallet": ONCHAIN_WALLET,
        "lnbitswallet": LNBITS_WALLET,
        "description": desc,
        "webhook": webhook,
        "completelink": completelink,
        "completelinktext": completelinktext,
        "custom_css": customcss,
        "time": 1440,
        "amount": sats_amount,
        "extra": '{"mempool_endpoint": "https://mempool.space", "network": "Mainnet"}',
    }

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": INVOICE_API_KEY,
    }

    #logger.info(body)
    #logger.info(headers)
    #logger.info(url)

    try:
        # Convert the body data to JSON format
        json_data = json.dumps(body)
        response = requests.post(
            url, data=json_data, headers=headers, timeout=10
        )  # set a timeout of 10 seconds

        # Check the response status code
        if response.status_code == 200:
            # Request was successful
            res_data = response.json()
            logger.info("Request was successful")
            # logger.info(res_data)
            charge_id = res_data["id"]
            response_url = LNBITS_URL + "/satspay/" + charge_id
            return response_url

        else:
            # Request failed
            resp_data = ("Request failed with status code:", response.status_code)
            resp_data += response.text
            # logger.info(resp_data)
            return resp_data
    except Exception as e:
        # logger.info(e)
        return str(e)


def is_https_url(url: str):
    if url.startswith("https://"):
        return True
    else:
        return False


######################################################################
# To use this section below, remove the "." from .exchange_rates and .cache
# in the import statements above and run from src/ directory
# uncomment import asyncio and asyncio.run(main()) below
#
# from exchange_rates import fiat_amount_as_satoshis
# from cache import cache
######################################################################

async def main():
    """
      For Testing use only
    """
    try:
        Fiat = "USD"  # Must be upper case
        Amount = 10  # Must be integer
        total = await fiat_amount_as_satoshis(Amount, Fiat.upper())
        logger.info(f"Fiat: {Fiat}  Amount: {Amount}")
        logger.info(f"Total: {total}")
        logger.info("test no description")
        res_url = await get_lnbits_satspay(total, "")
        if is_https_url(res_url):
            logger.info(f"Repsonse URL: {res_url}")
        else:
            logger.info(f"Error messsages: {res_url}")

        App_Description = "Invoice link"
        logger.info(f"test description: {App_Description}")
        res_url = await get_lnbits_satspay(total, App_Description)
        if is_https_url(res_url):
            logger.info(f"Repsonse URL: {res_url}")
        else:
            logger.info(f"Error messsages:{res_url}")

    except Exception as e:
        logger.error(f"running Main method exception: {e}")


#asyncio.run(main())
