# Data Dictionary - AgroConnect Project

This document provides a comprehensive data dictionary for the AgroConnect Django project database. It lists all tables (Django models), their fields, data types, constraints, descriptions, and relationships.

**Database:** SQLite (db.sqlite3)
**Generated from:** myadmin/models.py, user/models.py, chatbot/models.py

## Table Prefixes
- `myadmin_`: Admin/Farmer app models
- `user_`: Customer/User app models  
- `chatbot_`: Chatbot app models
- `auth_user`: Django built-in User model (used extensively)

## 1. auth_user (Django User Model - Summary)
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| username | CharField(150) | Unique | Login username |
| email | EmailField | Unique | User email |
| first_name | CharField(150) | - | First name |
| last_name | CharField(150) | - | Last name |
| password | CharField(128) | - | Hashed password |
| is_active | BooleanField | Default=True | Account active |
| date_joined | DateTimeField | Auto | Join date |

## 2. myadmin_sitesettings / user_sitesettings
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| notification_banner | TextField | Default text | Top banner notification text |
| is_notification_active | BooleanField | Default=True | Banner visibility flag |

## 3. myadmin_category / user_category
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| name | CharField | Max=100 | Category name |
| description | TextField | Null/Blank | Description |
| image | ImageField | Null/Blank, upload_to='categories/' | Category image |
| meta_title | CharField | Max=200, Null/Blank | SEO meta title |
| meta_description | TextField | Null/Blank | SEO meta desc |
| created_at | DateTimeField | Auto_now_add | Creation timestamp |

## 4. myadmin_product / user_product
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| name | CharField | Max=200 | Product name |
| farmer | ForeignKey | Null/Blank, to Farmer | Associated farmer |
| category | ForeignKey | to Category | Product category |
| description | TextField | Null/Blank | Product desc |
| additional_info | TextField | Null/Blank | JSON extra info |
| reviews | TextField | Null/Blank | JSON reviews |
| price | DecimalField | max_digits=10, places=2 | Current price |
| original_price | DecimalField | Null/Blank | Original price |
| image | ImageField | Null/Blank, upload_to='products/' | Product image |
| rating | FloatField | Default=5.0 | Average rating |
| is_new | BooleanField | Default=False | New product flag |
| is_hot | BooleanField | Default=False | Hot product flag |
| is_sale | BooleanField | Default=False | Sale flag |
| stock | IntegerField | Default=0/12 | Stock quantity |
| view_count | IntegerField | Default=0/9 | View count |
| sold_count | IntegerField | Default=0/4 | Sold count |
| sku | CharField | Max=50, Default | Stock keeping unit |
| tags | CharField | Max=200, Default | Product tags |
| created_at | DateTimeField | Auto_now_add | Creation timestamp |

## 5. myadmin_contact_us / user_contact_us
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| name | CharField | Max=100 | Contact name |
| email | EmailField | - | Email |
| phone | IntegerField / CharField | - | Phone number |
| message | TextField | - | Message content |
| is_read | BooleanField | Default=False | Admin read status |
| created_at | DateTimeField | Auto_now_add | Submission time |

## 6. myadmin_cart / user_cart
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| session_id | CharField | Max=100, Unique, Null/Blank | Session ID |
| user | ForeignKey | Null/Blank, to User | Associated user |
| created_at | DateTimeField | Auto_now_add | Creation time |
| updated_at | DateTimeField | Auto_now | Update time |

## 7. myadmin_cartitem / user_cartitem
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| cart | ForeignKey | to Cart | Parent cart |
| product | ForeignKey | to Product | Cart product |
| quantity | IntegerField | Default=1 | Quantity |
| created_at | DateTimeField | Auto_now_add | Add time |
| updated_at | DateTimeField | Auto_now | Update time |

## 8. myadmin_useraddress / user_useraddress
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| user | ForeignKey | to User | Owner |
| first_name | CharField | Max=100 | First name |
| last_name | CharField | Max=100 | Last name |
| address_line_1 | CharField | Max=255 | Address 1 |
| address_line_2 | CharField | Max=255, Null/Blank | Address 2 |
| city | CharField | Max=100 | City |
| state | CharField | Max=100 | State |
| postal_code | CharField | Max=20 | PIN/ZIP |
| country | CharField | Max=100, Default='India' | Country |
| phone | CharField | Max=20, Null/Blank | Phone |
| is_default | BooleanField | Default=False | Default address |
| created_at | DateTimeField | Auto_now_add | Creation time |
| updated_at | DateTimeField | Auto_now | Update time |

## 9. myadmin_wishlist / user_wishlist
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| user | ForeignKey | Null/Blank, to User | Owner |
| session_id | CharField | Max=100, Null/Blank | Session |
| product | ForeignKey | to Product | Wishlisted product |
| created_at | DateTimeField | Auto_now_add | Add time |
**Constraints:** unique_together(user, product)

## 10. myadmin_farmer
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| user | OneToOneField | to User | Linked user account |
| name | CharField | Max=200 | Farmer name |
| phone | CharField | Max=20 | Phone |
| address | TextField | Blank | Address |
| is_active | BooleanField | Default=True | Active status |
| created_at | DateTimeField | Auto_now_add | Registration time |

## 11. myadmin_order / user_order
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| order_number | CharField | Max=50, Unique | Order ID (e.g., ORD-ABC123) |
| user | ForeignKey | Null/Blank, to User | Customer |
| farmer | ForeignKey | Null/Blank, to Farmer | Seller farmer |
| session_id | CharField | Max=100, Null/Blank | Session |
| first_name | CharField | Max=100 | Billing first name |
| last_name | CharField | Max=100 | Billing last name |
| email | EmailField | - | Billing email |
| phone | CharField | Max=20 | Billing phone |
| address_line_1 | CharField | Max=255 | Shipping addr 1 |
| address_line_2 | CharField | Max=255, Null/Blank | Shipping addr 2 |
| city | CharField | Max=100 | City |
| state | CharField | Max=100 | State |
| postal_code | CharField | Max=20 | PIN |
| country | CharField | Max=100, Default='India' | Country |
| status | CharField | Max=20, Choices | Order status (pending, etc.) |
| subtotal | DecimalField | max_digits=10, places=2 | Items subtotal |
| shipping_cost | DecimalField | max_digits=10, places=2, Default=0 | Shipping fee |
| total | DecimalField | max_digits=10, places=2 | Grand total |
| payment_method | CharField | Max=50, Default='cod' | COD/Card/etc. |
| payment_status | CharField | Max=20, Default='pending' | Payment status |
| razorpay_payment_id | CharField | Max=100, Null/Blank | Razorpay ID |
| razorpay_order_id | CharField | Max=100, Null/Blank | Razorpay order |
| notes | TextField | Null/Blank | Order notes |
| created_at | DateTimeField | Auto_now_add | Order time |
| updated_at | DateTimeField | Auto_now | Update time |

## 12. myadmin_orderitem / user_orderitem
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| order | ForeignKey | to Order | Parent order |
| product | ForeignKey | to Product | Ordered product |
| quantity | IntegerField | Default=1 | Quantity |
| price | DecimalField | max_digits=10, places=2 | Price at order time |
| subtotal | DecimalField | max_digits=10, places=2 | Line total |

## 13. chatbot_chatconversation
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| session_id | CharField | Max=100, Unique | Chat session ID |
| user | ForeignKey | Null/Blank, to User | User |
| created_at | DateTimeField | Auto_now_add | Start time |
| updated_at | DateTimeField | Auto_now | Last activity |
| is_active | BooleanField | Default=True | Active session |

## 14. chatbot_chatmessage
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| conversation | ForeignKey | to ChatConversation | Parent session |
| message_type | CharField | Max=20, Choices (user/bot/system) | Sender type |
| message | TextField | - | Message text |
| timestamp | DateTimeField | Auto_now_add | Send time |
| metadata | JSONField | Null/Blank | Extra data (quick replies, etc.) |

## 15. chatbot_chatintent
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| name | CharField | Max=100, Unique | Intent name |
| patterns | TextField | - | Keywords/patterns (comma sep) |
| response_template | TextField | - | Bot response |
| action_type | CharField | Max=50, Null/Blank | Action (search_products, etc.) |
| priority | IntegerField | Default=0 | Matching priority |
| is_active | BooleanField | Default=True | Enabled |

## 16. chatbot_quickreply
| Field | Data Type | Constraints | Description |
|-------|-----------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| key | CharField | Max=50 | Unique key |
| label | CharField | Max=100 | Button text |
| response | TextField | - | Response to send |
| action | CharField | Max=50, Null/Blank | Linked action |
| icon | CharField | Max=50, Null/Blank | Icon class |
| order | IntegerField | Default=0 | Display order |

**Note:** Models are duplicated between myadmin and user apps, resulting in separate tables for admin/farmer vs user/customer contexts. Product/Farmer cross-references use app labels (e.g., 'myadmin.Farmer').
