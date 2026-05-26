"""
Advanced Chatbot Intelligence Engine
Natural Language Processing and Response Generation
"""
import re
import random
import json
from datetime import datetime
from django.db.models import Q
from django.utils import timezone
from difflib import SequenceMatcher

# Import models
from .models import ChatConversation, ChatMessage, ChatIntent, QuickReply
from user.models import Product, Category, Order


class ChatbotIntelligence:
    """Main chatbot intelligence class"""
    
    def __init__(self, session_id=None, user=None):
        self.session_id = session_id
        self.user = user
        self.conversation = None
        self.context = {}
        
    def get_or_create_conversation(self):
        """Get or create a chat conversation"""
        if self.session_id:
            self.conversation, created = ChatConversation.objects.get_or_create(
                session_id=self.session_id,
                defaults={'user': self.user}
            )
        return self.conversation
    
    def analyze_intent(self, user_message):
        """Analyze user message and determine intent"""
        message_lower = user_message.lower().strip()
        
        # Check for exact matches and patterns
        intent_patterns = {
            # Product Search
            'product_search': {
                'patterns': ['find', 'search', 'look for', 'buy', 'want', 'need', 'show', 'list', 'available', 'products', 'items'],
                'response': "I'll help you find products! What are you looking for? You can search by name, category, or describe what you need.",
                'action': 'search_products'
            },
            # Order Tracking
            'order_tracking': {
                'patterns': ['track', 'order status', 'where is', 'delivery', 'shipped', 'arriving', 'order number', 'ord-'],
                'response': "I can help you track your order! Please provide your order number (e.g., ORD-1234ABCD) or the email you used for ordering.",
                'action': 'track_order'
            },
            # Price Inquiry
            'price': {
                'patterns': ['price', 'cost', 'how much', 'rate', 'discount', 'offer', 'sale', 'cheap', 'expensive'],
                'response': "I can show you our product prices! Just search for any product and I'll show you the current pricing with any available discounts.",
                'action': 'show_prices'
            },
            # Category Browse
            'browse_categories': {
                'patterns': ['categories', 'category', 'types', 'varieties', 'kinds', 'sections', 'browse', 'collections'],
                'response': "We have various categories! Click on 'Shop' to see all categories including grains, spices, oils, fruits, vegetables, and more.",
                'action': 'browse_categories'
            },
            # Shopping Cart
            'cart': {
                'patterns': ['cart', 'basket', 'add to cart', 'remove', 'quantity', 'checkout', 'order'],
                'response': "You can view your cart by clicking the cart icon in the header. There you can modify quantities or proceed to checkout.",
                'action': 'view_cart'
            },
            # Wishlist
            'wishlist': {
                'patterns': ['wishlist', 'favorites', 'saved', 'like', 'heart', 'bookmark'],
                'response': "Click the heart icon on any product to add it to your wishlist! You can view your saved items anytime.",
                'action': 'view_wishlist'
            },
            # Help
            'help': {
                'patterns': ['help', 'support', 'assist', 'guide', 'how to', 'what can you do', 'commands'],
                'response': "I can help you with:\n• Finding products\n• Tracking orders\n• Checking prices\n• Managing cart & wishlist\n• Agricultural tips\n• General inquiries\n\nJust ask me anything!",
                'action': 'show_help'
            },
            # Contact
            'contact': {
                'patterns': ['contact', 'phone', 'email', 'reach', 'call', 'support team', 'customer service'],
                'response': "You can contact us at:\n• Phone: (234) 109-6666\n• Email: support@agroconnect.com\n• Visit our Contact page for more options.",
                'action': 'show_contact'
            },
            # Shipping
            'shipping': {
                'patterns': ['shipping', 'delivery', 'deliver', 'pickup', 'courier', 'time', 'days', 'free delivery'],
                'response': "We offer fast delivery across India! Standard delivery takes 3-5 business days. Free delivery available on orders above ₹500.",
                'action': 'show_shipping'
            },
            # Payment
            'payment': {
                'patterns': ['payment', 'pay', 'cod', 'online', 'card', 'upi', 'razorpay', 'money'],
                'response': "We accept multiple payment methods:\n• Cash on Delivery (COD)\n• Credit/Debit Cards\n• UPI\n• Net Banking\n• Wallets",
                'action': 'show_payment'
            },
            # Return/Refund
            'return': {
                'patterns': ['return', 'refund', 'exchange', 'cancel', 'replace', 'damaged', 'quality'],
                'response': "We have a 7-day return policy! If you're not satisfied with your purchase, you can request a return or exchange.",
                'action': 'show_returns'
            },
            # Organic Products
            'organic': {
                'patterns': ['organic', 'natural', 'chemical free', 'pure', 'fresh', 'farm fresh'],
                "response": "We prioritize quality! Most of our products are organically sourced directly from farmers. Look for 'Organic' badges on products.",
                'action': 'show_organic'
            },
            # Farming Tips
            'farming_tips': {
                'patterns': ['farming', 'cultivation', 'crop', 'agriculture', 'grow', 'plant', 'soil', 'harvest', 'tips', 'advice'],
                'response': "I'd be happy to share farming knowledge! What specific crop or agricultural topic would you like to know about?",
                'action': 'farming_tips'
            },
            # Weather (basic)
            'weather': {
                'patterns': ['weather', 'rain', 'monsoon', 'drought', 'climate', 'temperature'],
                'response': "For weather-specific farming advice, I recommend checking local weather forecasts. Would you like general seasonal farming tips?",
                'action': 'weather_info'
            },
            # Greetings
            'greeting': {
                'patterns': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'namaste', 'greetings'],
                'response': "Namaste! 👋 Welcome to AgroConnect! How can I help you today?",
                'action': 'greeting'
            },
            # Thanks
            'thanks': {
                'patterns': ['thank', 'thanks', 'thankyou', 'appreciate', 'grateful'],
                'response': "You're welcome! 😊 Is there anything else I can help you with?",
                'action': 'thanks'
            },
            # Goodbye
            'goodbye': {
                'patterns': ['bye', 'goodbye', 'see you', 'take care', 'later', 'exit'],
                'response': "Thank you for visiting AgroConnect! Feel free to return anytime. Happy farming! 🌱",
                'action': 'goodbye'
            },
        }
        
        # Check patterns for matches
        for intent_name, intent_data in intent_patterns.items():
            for pattern in intent_data['patterns']:
                if pattern in message_lower or message_lower in pattern:
                    return {
                        'intent': intent_name,
                        'response': intent_data['response'],
                        'action': intent_data['action'],
                        'confidence': 0.9
                    }
        
        # Check for order number in message
        order_match = re.search(r'ORD-[A-Z0-9]{8}', user_message, re.IGNORECASE)
        if order_match:
            return {
                'intent': 'order_lookup',
                'response': self._track_order_by_number(order_match.group()),
                'action': 'track_order',
                'confidence': 1.0
            }
        
        # Check for product search
        products = self._search_products(user_message)
        if products:
            return {
                'intent': 'product_found',
                'response': self._format_product_response(products, user_message),
                'action': 'show_products',
                'confidence': 0.8,
                'products': products[:5]
            }
        
        # Default response with suggestions
        return {
            'intent': 'general',
            'response': self._generate_fallback_response(user_message),
            'action': 'general',
            'confidence': 0.3
        }
    
    def _search_products(self, query, limit=10):
        """Search products by name or description"""
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(tags__icontains=query),
            stock__gt=0
        )[:limit]
        return list(products)
    
    def _track_order_by_number(self, order_number):
        """Track order by order number"""
        try:
            order = Order.objects.get(order_number__iexact=order_number)
            status_emoji = {
                'pending': '⏳',
                'processing': '📦',
                'shipped': '🚚',
                'delivered': '✅',
                'cancelled': '❌'
            }
            emoji = status_emoji.get(order.status, '📦')
            return (f"Order {order.order_number} Status:\n\n"
                   f"📍 Status: {emoji} {order.status.title()}\n"
                   f"📅 Ordered: {order.created_at.strftime('%d %b %Y')}\n"
                   f"💰 Total: ₹{order.total}\n"
                   f"🏠 Shipping to: {order.city}, {order.state}\n\n"
                   f"Would you like more details?")
        except Order.DoesNotExist:
            return "I couldn't find an order with that number. Please check and try again, or contact support."
    
    def _format_product_response(self, products, query):
        """Format product search results"""
        if not products:
            return f"I couldn't find any products matching '{query}'. Try a different search term or browse our categories."
        
        response = f"🌾 I found {len(products)} products matching '{query}':\n\n"
        for i, product in enumerate(products, 1):
            price_str = f"₹{product.price}"
            if product.original_price and product.original_price > product.price:
                price_str = f"~~₹{product.original_price}~~ ₹{product.price} (-{int((1-product.price/product.original_price)*100)}%)"
            
            badges = []
            if product.is_new:
                badges.append("🆕")
            if product.is_hot:
                badges.append("🔥")
            if product.is_sale:
                badges.append("🏷️")
            
            badge_str = " ".join(badges) + " " if badges else ""
            response += f"{i}. {badge_str}{product.name}\n   💰 {price_str} | 📦 {product.stock} in stock\n\n"
        
        response += "Would you like to view more details or add any to your cart?"
        return response
    
    def _generate_fallback_response(self, message):
        """Generate intelligent fallback for unrecognized messages"""
        fallbacks = [
            "I'm here to help! You can ask me about:\n• Products & prices\n• Order tracking\n• Shopping assistance\n• Farming tips\n\nWhat would you like to know?",
            "I didn't quite catch that. Try asking about our products, tracking an order, or browse our categories!",
            "I'm your farming assistant! Ask me anything about our products, orders, or agricultural topics.",
            "Let me help you find what you need! Search for products, ask about your order, or tell me what you're looking for.",
        ]
        return random.choice(fallbacks)
    
    def get_quick_replies(self):
        """Get quick reply options for the user"""
        quick_replies = [
            {'key': 'shop', 'label': '🛒 Browse Products', 'action': 'browse_shop'},
            {'key': 'categories', 'label': '📂 All Categories', 'action': 'show_categories'},
            {'key': 'track', 'label': '📦 Track Order', 'action': 'track_order'},
            {'key': 'cart', 'label': '🛍️ View Cart', 'action': 'view_cart'},
            {'key': 'help', 'label': '❓ Help', 'action': 'show_help'},
            {'key': 'contact', 'label': '📞 Contact Us', 'action': 'show_contact'},
        ]
        return quick_replies
    
    def process_message(self, user_message):
        """Process user message and generate response"""
        # Get or create conversation
        self.get_or_create_conversation()
        
        # Save user message
        if self.conversation:
            ChatMessage.objects.create(
                conversation=self.conversation,
                message_type='user',
                message=user_message
            )
        
        # Analyze intent and get response
        intent_data = self.analyze_intent(user_message)
        
        # Create bot response
        bot_response = intent_data['response']
        
        # Get quick replies
        quick_replies = self.get_quick_replies()
        
        # Save bot response
        if self.conversation:
            ChatMessage.objects.create(
                conversation=self.conversation,
                message_type='bot',
                message=bot_response,
                metadata={'intent': intent_data['intent'], 'action': intent_data.get('action')}
            )
        
        return {
            'response': bot_response,
            'intent': intent_data['intent'],
            'action': intent_data.get('action'),
            'quick_replies': quick_replies,
            'products': intent_data.get('products', [])
        }
    
    def get_conversation_history(self, limit=20):
        """Get conversation history"""
        if not self.conversation:
            return []
        
        messages = ChatMessage.objects.filter(
            conversation=self.conversation
        ).order_by('-timestamp')[:limit]
        
        return [{
            'type': msg.message_type,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat()
        } for msg in reversed(messages)]


class FarmingKnowledgeBase:
    """Agricultural knowledge base for farming tips"""
    
    @staticmethod
    def get_tip(crop_type=None):
        """Get farming tips based on crop type"""
        tips = {
            'rice': [
                "For rice cultivation, maintain water level at 2-5cm during early growth stages.",
                "Use System of Rice Intensification (SRI) method for higher yields with less water.",
                "Apply nitrogen fertilizer in 3 split doses for better utilization.",
            ],
            'wheat': [
                "wheat is best sown in optimal moisture conditions. Avoid sowing in dry soil.",
                "Recommended seed rate is 100-125 kg/ha for bread wheat.",
                "Apply zinc sulfate at 25 kg/ha if deficiency is observed.",
            ],
            'vegetables': [
                "Use drip irrigation for vegetables to save water and reduce disease.",
                "Practice crop rotation to prevent soil-borne diseases.",
                "Mulching helps retain moisture and suppress weeds.",
            ],
            'general': [
                "Test your soil annually to understand nutrient requirements.",
                "Use organic compost to improve soil health and structure.",
                "Integrated Pest Management (IPM) reduces chemical usage.",
                "Proper spacing between plants ensures better air circulation.",
                "Water plants early morning or evening to reduce evaporation loss.",
            ]
        }
        
        if crop_type:
            crop_lower = crop_type.lower()
            for key in tips:
                if key in crop_lower:
                    return random.choice(tips[key])
        
        return random.choice(tips['general'])


def initialize_default_intents():
    """Initialize default chatbot intents"""
    default_intents = [
        {
            'name': 'greeting',
            'patterns': 'hello,hi,hey,good morning,good afternoon,namaste',
            'response': 'Namaste! Welcome to AgroConnect! How can I help you today?',
            'priority': 10
        },
        {
            'name': 'product_search',
            'patterns': 'find,search,look for,buy,products,show items',
            'response': "I'll help you find products! What are you looking for?",
            'priority': 8
        },
        {
            'name': 'order_tracking',
            'patterns': 'track,order status,delivery,shipped',
            'response': "Please provide your order number to track your order.",
            'priority': 9
        },
        {
            'name': 'help',
            'patterns': 'help,support,assist,how to',
            'response': "I can help you with products, orders, and farming tips!",
            'priority': 7
        },
    ]
    
    for intent_data in default_intents:
        ChatIntent.objects.get_or_create(
            name=intent_data['name'],
            defaults={
                'patterns': intent_data['patterns'],
                'response_template': intent_data['response'],
                'priority': intent_data['priority']
            }
        )


def initialize_quick_replies():
    """Initialize default quick replies"""
    default_replies = [
        {'key': 'shop', 'label': '🛒 Browse Products', 'response': 'Let me show you our products!', 'action': 'browse_shop', 'order': 1},
        {'key': 'categories', 'label': '📂 All Categories', 'response': 'Here are our categories!', 'action': 'show_categories', 'order': 2},
        {'key': 'track', 'label': '📦 Track Order', 'response': 'Please provide your order number.', 'action': 'track_order', 'order': 3},
        {'key': 'cart', 'label': '🛍️ View Cart', 'response': 'Opening your cart...', 'action': 'view_cart', 'order': 4},
        {'key': 'help', 'label': '❓ Help', 'response': 'I can help you with many things!', 'action': 'show_help', 'order': 5},
        {'key': 'contact', 'label': '📞 Contact Us', 'response': 'Here is our contact information.', 'action': 'show_contact', 'order': 6},
    ]
    
    for reply_data in default_replies:
        QuickReply.objects.get_or_create(
            key=reply_data['key'],
            defaults=reply_data
        )
