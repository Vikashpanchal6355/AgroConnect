"""
Advanced Chatbot Views
Handles chatbot API requests and responses
"""
import json
import uuid

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from user.models import Order, Product

from .intelligence import ChatbotIntelligence, initialize_default_intents, initialize_quick_replies
from .models import ChatConversation, ChatMessage, QuickReply


def chatbot_view(request):
    """Render the chatbot page."""
    initialize_default_intents()
    initialize_quick_replies()

    session_id = request.session.session_key or str(uuid.uuid4())
    if not request.session.session_key:
        request.session.create()
        session_id = request.session.session_key

    context = {
        "session_id": session_id,
        "user": request.user if request.user.is_authenticated else None,
    }
    return render(request, "chatbot/chatbot.html", context)


@csrf_exempt
@require_POST
def chatbot_api(request):
    """Main chatbot API endpoint."""
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        session_id = data.get("session_id", "")

        if not user_message:
            return JsonResponse({"success": False, "error": "Message is required"})

        chatbot = ChatbotIntelligence(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None,
        )
        result = chatbot.process_message(user_message)

        return JsonResponse(
            {
                "success": True,
                "response": result["response"],
                "intent": result["intent"],
                "action": result["action"],
                "quick_replies": result["quick_replies"],
                "products": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "price": str(product.price),
                        "original_price": str(product.original_price) if product.original_price else None,
                        "image": product.image.url if product.image else None,
                        "category": product.category.name if product.category else None,
                    }
                    for product in result.get("products", [])
                ],
            }
        )
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON format"})
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)})


@csrf_exempt
@require_POST
def chatbot_quick_reply(request):
    """Handle quick reply button clicks."""
    try:
        data = json.loads(request.body)
        action = data.get("action", "")
        session_id = data.get("session_id", "")

        chatbot = ChatbotIntelligence(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None,
        )

        responses = {
            "browse_shop": "Great! Let me take you to our shop. You can browse all products or filter by category.",
            "show_categories": "Here are our categories:\n\n- Grains & Pulses\n- Spices & Condiments\n- Oils\n- Fresh Fruits\n- Vegetables\n- Dry Fruits & Nuts\n- Ready to Eat\n\nWhich category interests you?",
            "track_order": "To track your order, please provide:\n\n- Your Order Number (e.g., ORD-1234ABCD)\n- Or the email used for ordering\n\nYou can also track from the 'Order Tracking' page.",
            "view_cart": "Here's your cart! You can view all your selected items here.",
            "show_help": "I can help you with:\n\n- Finding products\n- Tracking orders\n- Checking prices\n- Managing cart and wishlist\n- Agricultural tips\n- Contact information\n- Payment methods\n- Shipping info\n\nWhat would you like to know?",
            "show_contact": "Contact us:\n\n- Phone: (234) 109-6666\n- Email: support@agroconnect.com\n- Hours: Mon-Sat, 9AM-6PM IST\n\nVisit our Contact page for more options!",
        }

        return JsonResponse(
            {
                "success": True,
                "response": responses.get(action, "How can I help you?"),
                "action": action,
                "quick_replies": chatbot.get_quick_replies(),
            }
        )
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)})


@csrf_exempt
@require_POST
def chatbot_search_products(request):
    """Search products via chatbot."""
    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()

        if not query:
            return JsonResponse({"success": False, "error": "Search query is required"})

        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(tags__icontains=query),
            stock__gt=0,
        )[:10]

        results = []
        for product in products:
            price_str = f"₹{product.price}"
            if product.original_price and product.original_price > product.price:
                price_str = f"₹{product.original_price} -> ₹{product.price}"

            results.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "price": str(product.price),
                    "original_price": str(product.original_price) if product.original_price else None,
                    "image": product.image.url if product.image else None,
                    "category": product.category.name if product.category else None,
                    "stock": product.stock,
                    "price_display": price_str,
                }
            )

        return JsonResponse({"success": True, "products": results, "count": len(results)})
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)})


@csrf_exempt
@require_POST
def chatbot_track_order(request):
    """Track order via chatbot."""
    try:
        data = json.loads(request.body)
        order_number = data.get("order_number", "").strip().upper()

        if not order_number:
            return JsonResponse({"success": False, "error": "Order number is required"})

        try:
            order = Order.objects.get(order_number__iexact=order_number)
        except Order.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Order not found. Please check the order number and try again.",
                }
            )

        status_info = {
            "pending": {"text": "Order Placed", "emoji": "Pending"},
            "processing": {"text": "Processing", "emoji": "Processing"},
            "shipped": {"text": "Shipped", "emoji": "Shipped"},
            "delivered": {"text": "Delivered", "emoji": "Delivered"},
            "cancelled": {"text": "Cancelled", "emoji": "Cancelled"},
        }
        status_data = status_info.get(order.status, {"text": order.status, "emoji": "Updated"})

        return JsonResponse(
            {
                "success": True,
                "order": {
                    "order_number": order.order_number,
                    "status": order.status,
                    "status_text": status_data["text"],
                    "status_emoji": status_data["emoji"],
                    "total": str(order.total),
                    "created_at": order.created_at.strftime("%d %b %Y, %I:%M %p"),
                    "city": order.city,
                    "state": order.state,
                    "items_count": order.items.count(),
                },
            }
        )
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)})


@csrf_exempt
@require_POST
def chatbot_conversation_history(request):
    """Get conversation history."""
    try:
        data = json.loads(request.body)
        session_id = data.get("session_id", "")

        try:
            conversation = ChatConversation.objects.get(session_id=session_id)
        except ChatConversation.DoesNotExist:
            return JsonResponse({"success": True, "history": []})

        messages = ChatMessage.objects.filter(conversation=conversation).order_by("timestamp")[:50]
        history = [
            {
                "type": msg.message_type,
                "message": msg.message,
                "timestamp": msg.timestamp.strftime("%I:%M %p"),
            }
            for msg in messages
        ]
        return JsonResponse({"success": True, "history": history})
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)})

