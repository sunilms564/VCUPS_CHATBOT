from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

inprogress_orders = {}

@app.post("/")
async def handle_request(request: Request):
    try:
        # Retrieve the JSON data from the request
        payload = await request.json()

        # Extract necessary information from the payload
        intent = payload['queryResult']['intent']['displayName']
        parameters = payload['queryResult']['parameters']
        output_contexts = payload['queryResult']['outputContexts']
        session_id = generic_helper.extract_session_id(output_contexts[0]["name"])

        intent_handler_dict = {
            'order.add': add_to_order,
            'order.remove': remove_from_order,
            'order.complete': complete_order,
            'track.order': track_order
        }

        if intent in intent_handler_dict:
            return intent_handler_dict[intent](parameters, session_id)
        else:
            raise HTTPException(status_code=400, detail="Intent not recognized")

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


def save_order_to_db(order: dict) -> int:
    next_order_id = db_helper.get_next_order_id()

    # Insert individual items along with quantity in orders table
    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1

    # Now insert order tracking status
    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id

def complete_order(parameters: dict, session_id: str) -> JSONResponse:
    try:
        if session_id not in inprogress_orders:
            fulfillment_text = "I'm having trouble finding your order. Please place a new order."
        else:
            order = inprogress_orders[session_id]
            order_id = save_order_to_db(order)
            if order_id == -1:
                fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                                   "Please place a new order."
            else:
                order_total = db_helper.get_total_order_price(order_id)
                fulfillment_text = f"Your order has been placed with order id: {order_id}. " \
                                   f"Total amount payable is {order_total}. Thank you!"

            del inprogress_orders[session_id]

        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


def add_to_order(parameters: dict, session_id: str) -> JSONResponse:
    try:
        food_items = parameters.get("food-item", [])
        quantities = parameters.get("number", [])

        if len(food_items) != len(quantities):
            fulfillment_text = "Please specify food items and quantities clearly."
        else:
            new_order = dict(zip(food_items, quantities))
            if session_id in inprogress_orders:
                inprogress_orders[session_id].update(new_order)
            else:
                inprogress_orders[session_id] = new_order

            order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
            fulfillment_text = f"Your current order: {order_str}. Anything else?"

        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


def remove_from_order(parameters: dict, session_id: str) -> JSONResponse:
    try:
        if session_id not in inprogress_orders:
            return JSONResponse(content={"fulfillmentText": "No order found. Please place a new order."})

        food_items = parameters.get("food-item", [])
        current_order = inprogress_orders[session_id]

        removed_items = []
        not_in_order = []

        for item in food_items:
            if item not in current_order:
                not_in_order.append(item)
            else:
                removed_items.append(item)
                del current_order[item]

        if len(removed_items) > 0:
            fulfillment_text = f"Removed {', '.join(removed_items)} from your order."

        if len(not_in_order) > 0:
            fulfillment_text = f"No such items {', '.join(not_in_order)} in your current order."

        if len(current_order) == 0:
            fulfillment_text += " Your order is empty!"
        else:
            order_str = generic_helper.get_str_from_food_dict(current_order)
            fulfillment_text += f" Your updated order: {order_str}"

        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


def track_order(parameters: dict, session_id: str) -> JSONResponse:
    try:
        order_id = int(parameters.get('order_id', 0))
        order_status = db_helper.get_order_status(order_id)
        if order_status:
            fulfillment_text = f"The order status for order id {order_id} is: {order_status}"
        else:
            fulfillment_text = f"No order found with order id {order_id}"

        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
