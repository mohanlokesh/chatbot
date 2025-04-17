# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

"""
Custom actions for Rasa to interact with PostgreSQL database
"""
import os
import sys
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from dotenv import load_dotenv

# Add parent directory to path to import database models
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.models import User, Order, OrderItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Configure database connection
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)


class ActionCheckOrderStatus(Action):
    """Action to check order status by order number"""

    def name(self) -> Text:
        return "action_check_order_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get order number from slot
        order_number = tracker.get_slot("order_number")
        
        if not order_number:
            dispatcher.utter_message(text="I need an order number to check the status. Can you provide your order number?")
            return []
        
        # Query database for order information
        session = Session()
        try:
            order = session.query(Order).filter_by(order_number=order_number).first()
            
            if not order:
                dispatcher.utter_message(text=f"I couldn't find an order with number {order_number}. Please check the number and try again.")
                return []
            
            # Format response based on order status
            status_message = f"Your order #{order_number} is currently {order.status.value}."
            
            if order.status.name == "SHIPPED":
                status_message += f" It was shipped on {order.ordered_at.strftime('%B %d, %Y')}."
                if order.tracking_number:
                    status_message += f" Your tracking number is {order.tracking_number}."
            
            elif order.status.name == "DELIVERED":
                status_message += f" It was delivered on {order.delivered_at.strftime('%B %d, %Y')}."
            
            elif order.status.name == "PROCESSING":
                status_message += f" It should be shipped soon."
                if order.estimated_delivery:
                    status_message += f" Estimated delivery date is {order.estimated_delivery.strftime('%B %d, %Y')}."
            
            dispatcher.utter_message(text=status_message)
            
            return [SlotSet("order_status", order.status.value)]
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while checking your order: {str(e)}")
            return []
        finally:
            session.close()


class ActionHandleOrderStatus(Action):
    """
    Alternative implementation for handling order status.
    This is a compatibility action to resolve conflicts in stories.
    """

    def name(self) -> Text:
        return "action_handle_order_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Simply delegate to ActionCheckOrderStatus for consistency
        action = ActionCheckOrderStatus()
        return action.run(dispatcher, tracker, domain)


class ActionListOrderItems(Action):
    """Action to list items in an order"""

    def name(self) -> Text:
        return "action_list_order_items"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get order number from slot
        order_number = tracker.get_slot("order_number")
        
        if not order_number:
            dispatcher.utter_message(text="I need an order number to list the items. Can you provide your order number?")
            return []
        
        # Query database for order items
        session = Session()
        try:
            order = session.query(Order).filter_by(order_number=order_number).first()
            
            if not order:
                dispatcher.utter_message(text=f"I couldn't find an order with number {order_number}. Please check the number and try again.")
                return []
            
            if not order.order_items:
                dispatcher.utter_message(text=f"Your order #{order_number} doesn't have any items.")
                return []
            
            # Format response with order items
            response = f"Your order #{order_number} contains the following items:\n"
            
            for item in order.order_items:
                response += f"- {item.quantity}x {item.product_name} (${item.price:.2f} each)\n"
            
            response += f"\nTotal: ${order.total_amount:.2f}"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while listing your order items: {str(e)}")
            return []
        finally:
            session.close()


class ActionGetUserOrders(Action):
    """Action to get all orders for a user"""

    def name(self) -> Text:
        return "action_get_user_orders"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get user email from slot
        user_email = tracker.get_slot("user_email")
        
        if not user_email:
            dispatcher.utter_message(text="I need your email address to look up your orders. Can you provide your email?")
            return []
        
        # Query database for user orders
        session = Session()
        try:
            user = session.query(User).filter_by(email=user_email).first()
            
            if not user:
                dispatcher.utter_message(text=f"I couldn't find a user with email {user_email}. Please check your email and try again.")
                return []
            
            if not user.orders:
                dispatcher.utter_message(text=f"You don't have any orders associated with this email address.")
                return []
            
            # Format response with user orders
            recent_orders = sorted(user.orders, key=lambda o: o.ordered_at, reverse=True)[:5]
            
            response = f"Here are your most recent orders:\n"
            
            for order in recent_orders:
                response += f"- Order #{order.order_number}: {order.status.value}, placed on {order.ordered_at.strftime('%B %d, %Y')}, total: ${order.total_amount:.2f}\n"
            
            response += "\nYou can ask me about a specific order by providing the order number."
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while retrieving your orders: {str(e)}")
            return []
        finally:
            session.close()
