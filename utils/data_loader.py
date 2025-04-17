"""
Utility functions for loading FAQ data for chatbot testing
"""

import os
import json

def load_faq_data(faq_path=None):
    """
    Load FAQ data from a JSON file or use sample data if file not found
    
    Args:
        faq_path (str, optional): Path to JSON file with FAQ data
        
    Returns:
        list: List of FAQ dictionaries with question and answer keys
    """
    # If path provided, try to load from file
    if faq_path and os.path.exists(faq_path):
        try:
            with open(faq_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading FAQ data from {faq_path}: {e}")
            print("Using sample data instead.")
    
    # Return sample FAQs
    return [
        {
            "question": "What is your return policy?",
            "answer": "You can return items within 30 days of delivery for a full refund. Items must be unused and in original packaging.",
            "category": "Returns"
        },
        {
            "question": "How do I track my order?",
            "answer": "You can track your order by logging into your account and going to the 'Order History' section. You'll find tracking information for shipped orders there.",
            "category": "Shipping"
        },
        {
            "question": "Do you offer free shipping?",
            "answer": "Yes, we offer free standard shipping on all orders over $50. Orders under $50 have a flat shipping fee of $4.99.",
            "category": "Shipping"
        },
        {
            "question": "How can I use a promo code?",
            "answer": "You can enter a promo code during checkout on the payment page. Look for the 'Apply Promo Code' field, enter your code, and click 'Apply'.",
            "category": "Payment"
        },
        {
            "question": "What payment methods do you accept?",
            "answer": "We accept all major credit cards (Visa, Mastercard, American Express), PayPal, and Apple Pay.",
            "category": "Payment"
        },
        {
            "question": "How long does shipping take?",
            "answer": "Standard shipping typically takes 3-5 business days. Expedited shipping takes 1-2 business days. International shipping can take 7-14 business days.",
            "category": "Shipping"
        },
        {
            "question": "Do you ship internationally?",
            "answer": "Yes, we ship to most countries worldwide. International shipping rates vary by destination and are calculated at checkout.",
            "category": "Shipping"
        },
        {
            "question": "How do I request a refund?",
            "answer": "To request a refund, go to your account, find the order in your order history, and click the 'Return Items' button. Follow the prompts to complete your refund request.",
            "category": "Returns"
        },
        {
            "question": "Can I change or cancel my order?",
            "answer": "You can change or cancel your order within 1 hour of placing it. After that, please contact customer support for assistance.",
            "category": "Orders"
        },
        {
            "question": "Do you have a mobile app?",
            "answer": "Yes, our mobile app is available for both iOS and Android devices. You can download it from the App Store or Google Play Store.",
            "category": "Website"
        }
    ] 