#!/usr/bin/env python
import re

with open('farmer_Shop/user/template/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix Home navigation
old_home_nav = '''                                        <li class="item has-child ">
                                                <a href="javascript:void(0)">Home</a>
                                                <ul class="sub-nav">
                                                    <li class="">
                                                        <a href="index.html">
                                                            <span>
                                                                Home 1
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li><a href="home-2.html"><span>
                                                                Home 2
                                                            </span>
                                                        </a></li>
                                                    <li><a href="home-3.html"><span>
                                                                Home 3
                                                            </span>
                                                        </a></li>
                                                </ul>
                                            </li>'''

new_home_nav = '''                                        <li class="item has-child {% if current_page == 'index' %}current-menu{% endif %}">
                                                <a href="{% url 'index' %}">Home</a>
                                            </li>'''

content = content.replace(old_home_nav, new_home_nav)

# Fix Page dropdown to About Us link
old_page_nav = '''                                        <li class="item has-child">
                                                <a href="javascript:void(0)">Page</a>
                                                <ul class="sub-nav">
                                                    <li>
                                                        <a href="about-us.html">
                                                            <span>
                                                                About Us
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="our-commitments.html">
                                                            <span>
                                                                Our Commitments
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="our-events.html">
                                                            <span>
                                                                Our Events
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="our-farmers.html">
                                                            <span>
                                                                Our Farmers
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="our-history.html">
                                                            <span>
                                                                Our History
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="coming-soon.html">
                                                            <span>
                                                                Coming Soon
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="404.html">
                                                            <span>
                                                                404
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="event-detail.html">
                                                            <span>
                                                                Event Detail
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="faq.html">
                                                            <span>
                                                                FAQs
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="gallery.html">
                                                            <span>
                                                                Gallery
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="testimonial.html">
                                                            <span>
                                                                Testimonial
                                                            </span>
                                                        </a>
                                                    </li>
                                                </ul>
                                            </li>'''

new_page_nav = '''                                        <li class="item has-child {% if current_page == 'about_us' %}current-menu{% endif %}">
                                                <a href="{% url 'about_us' %}">About Us</a>
                                            </li>'''

content = content.replace(old_page_nav, new_page_nav)

# Fix Portfolio dropdown
old_portfolio_nav = '''                                        <li class="item has-child">
                                                <a href="javascript:void(0)">Portfolio</a>
                                                <ul class="sub-nav">

                                                    <li>
                                                        <a href="portfolio-style-1.html">
                                                            <span>
                                                                Portfolio Style 1
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="portfolio-style-2.html">
                                                            <span>
                                                                Portfolio Style 2
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="portfolio-style-3.html">
                                                            <span>
                                                                Portfolio Style 3
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="portfolio-details.html">
                                                            <span>
                                                                Portfolio Details
                                                            </span>
                                                        </a>
                                                    </li>
                                                </ul>
                                            </li>'''

new_portfolio_nav = '''                                        <li class="item has-child {% if current_page == 'portfolio' %}current-menu{% endif %}">
                                                <a href="{% url 'portfolio' %}">Portfolio</a>
                                                <ul class="sub-nav">
                                                    <li class="{% if current_page == 'portfolio_details' %}current-menu{% endif %}">
                                                        <a href="{% url 'portfolio_details' %}">
                                                            <span>
                                                                Portfolio Details
                                                            </span>
                                                        </a>
                                                    </li>
                                                </ul>
                                            </li>'''

content = content.replace(old_portfolio_nav, new_portfolio_nav)

# Fix Shop dropdown
old_shop_nav = '''                                        <li class="item has-child current-menu">
                                                <a href="javascript:void(0)">Shop</a>
                                                <ul class="sub-nav">

                                                    <li class="current-item"><a href="shop-products.html"><span>Shop
                                                                Products</span></a></li>
                                                    <li><a href="shop-details.html"><span>Shop
                                                                Details</span></a></li>
                                                    <li><a href="shop-cart.html"><span>Shop Cart</span></a></li>
                                                    <li><a href="wishlist.html"><span>Wishlist</span></a></li>
                                                    <li><a href="checkout.html"><span>Checkout</span></a></li>
                                                    <li><a href="order-tracking.html"><span>Order Tracking</span></a>
                                                    </li>
                                                    <li><a href="my-account.html"><span>My Account</span></a></li>
                                                    <li><a href="order-details.html"><span>Order Detail</span></a></li>
                                                </ul>
                                            </li>'''

new_shop_nav = '''                                        <li class="item has-child {% if current_page == 'shop' %}current-menu{% endif %}">
                                                <a href="{% url 'shop_products' %}">Shop</a>
                                                <ul class="sub-nav">
                                                    <li class="{% if current_page == 'shop_products' %}current-menu{% endif %}">
                                                        <a href="{% url 'shop_products' %}"><span>Shop Products</span></a>
                                                    </li>
                                                    <li class="{% if current_page == 'shop_cart' %}current-menu{% endif %}">
                                                        <a href="{% url 'shop_cart' %}"><span>Shop Cart</span></a>
                                                    </li>
                                                    <li class="{% if current_page == 'wishlist' %}current-menu{% endif %}">
                                                        <a href="{% url 'wishlist' %}"><span>Wishlist</span></a>
                                                    </li>
                                                    <li class="{% if current_page == 'checkout' %}current-menu{% endif %}">
                                                        <a href="{% url 'checkout' %}"><span>Checkout</span></a>
                                                    </li>
                                                    <li class="{% if current_page == 'order_tracking' %}current-menu{% endif %}">
                                                        <a href="{% url 'order_tracking' %}"><span>Order Tracking</span></a>
                                                    </li>
                                                    <li class="{% if current_page == 'my_account' %}current-menu{% endif %}">
                                                        <a href="{% url 'my_account' %}"><span>My Account</span></a>
                                                    </li>
                                                    <li class="{% if current_page == 'order_details' %}current-menu{% endif %}">
                                                        <a href="{% url 'order_details' %}"><span>Order Detail</span></a>
                                                    </li>
                                                </ul>
                                            </li>'''

content = content.replace(old_shop_nav, new_shop_nav)

# Fix Services dropdown
old_services_nav = '''                                        <li class="item has-child">
                                                <a href="javascript:void(0)">Services</a>
                                                <ul class="sub-nav">
                                                    <li>
                                                        <a href="our-services.html">
                                                            <span>
                                                                Our Services
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="service-detail.html">
                                                            <span>
                                                                Service Detail
                                                            </span>
                                                        </a>
                                                    </li>
                                                </ul>
                                            </li>'''

new_services_nav = '''                                        <li class="item has-child {% if current_page == 'our_services' %}current-menu{% endif %}">
                                                <a href="{% url 'our_services' %}">Services</a>
                                                <ul class="sub-nav">
                                                    <li class="{% if current_page == 'service_detail' %}current-menu{% endif %}">
                                                        <a href="{% url 'service_detail' %}">
                                                            <span>
                                                                Service Detail
                                                            </span>
                                                        </a>
                                                    </li>
                                                </ul>
                                            </li>'''

content = content.replace(old_services_nav, new_services_nav)

# Fix Blog dropdown (remove it)
old_blog_nav = '''                                        <li class="item has-child ">
                                                <a href="javascript:void(0)">Blog</a>
                                                <ul class="sub-nav">
                                                    <li>
                                                        <a href="blog-full-width.html">
                                                            <span>
                                                                Blog Full Width
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li class="">
                                                        <a href="blog-right-sidebar.html">
                                                            <span>
                                                                Blog Right Sidebar
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="blog-single.html">
                                                            <span>
                                                                Blog Single
                                                            </span>
                                                        </a>
                                                    </li>
                                                </ul>
                                            </li>'''

content = content.replace(old_blog_nav, '')

with open('farmer_Shop/user/template/base.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Navigation fixed successfully!")
