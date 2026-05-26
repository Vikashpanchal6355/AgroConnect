# UML & System Diagrams - AgroConnect Project
**BE Sem 8 College Report**  
**Project:** AgroConnect E-Commerce Platform  
**Generated:** Auto-generated comprehensive diagrams based on Django models and PROJECT_REPORT.md  

---

## 1. Use Case Diagram
**Actors:** Customer, Farmer, Admin, Guest  
**Primary Use Cases:**

```mermaid
graph TD
    A[Customer] --> B[View Products]
    A --> C[Search Products]
    A --> D[Add to Cart]
    A --> E[Manage Wishlist]
    A --> F[Checkout & Order]
    A --> G[Chat with Bot]
    A --> H[Manage Addresses]
    
    I[Farmer] --> J[Register as Farmer]
    I --> K[Manage Products]
    I --> L[View Orders]
    I --> M[Update Order Status]
    
    N[Admin] --> O[Manage Dashboard]
    N --> P[CRUD Categories]
    N --> Q[CRUD Products]
    N --> R[Manage All Orders]
    N --> S[Site Settings]
    
    T[Guest] --> B
    T --> C
    T --> U[Register/Login]
    
    style A fill:#e1f5fe
    style I fill:#f3e5f5
    style N fill:#fff3e0
```

**Descriptions:**
| Use Case | Pre-condition | Post-condition | Actors |
|----------|---------------|----------------|--------|
| View Products | None | Product list displayed | Customer, Guest |
| Checkout | Items in cart | Order created, payment initiated | Customer |
| Manage Products | Farmer login | Product updated in DB | Farmer |
| Manage Orders | Admin login | Order status updated | Admin |

---

## 2. Data Flow Diagrams (DFD)

### Level 0: Context Diagram
```mermaid
graph LR
    A[Customer/Farmer/Guest] -->|Browse/Add Cart/Order| SYS[AgroConnect System]
    SYS -->|Products/Orders/Status| A
    B[Admin] <-->|Manage Data| SYS
    SYS <-->|CRUD Operations| DB[(SQLite DB)]
```

### Level 1: Main Processes
```mermaid
graph TD
    A[User Input] --> P1[1.0 Product Catalog]
    A --> P2[2.0 Shopping Cart]
    A --> P3[3.0 Order Processing]
    A --> P4[4.0 Admin Management]
    
    P1 --> D1[(Product DB)]
    P2 --> D1
    P3 --> D2[(Order DB)]
    P4 --> D1
    P4 --> D2
    P4 --> D3[(User DB)]
    
    P3 --> EXT[External Payment Gateway]
```

### Level 2: Order Processing
```mermaid
graph TD
    A[Customer Checkout] --> B{Validate Cart}
    B -->|Valid| C[Create Order]
    B -->|Invalid| A
    C --> D[Save Order + Items]
    D --> E[Calculate Total]
    E --> F[Payment Gateway]
    F -->|Success| G[Update Status: Confirmed]
    F -->|Failed| H[Update Status: Failed]
    G --> I[Send Confirmation]
    H --> J[Notify Customer]
```

**ASCII Level 2 Alternative:**
```
Customer → Validate Cart → Create Order Record → DB
                    ↓
              Payment Gateway (Razorpay)
                    ↓
              Update Order Status → Email Notification
```

---

## 3. Entity-Relationship (ER) Diagram
**Based on DATA_DICTIONARY.md models**

```mermaid
erDiagram
    USER ||--o{ PRODUCT : "sells (farmer)"
    USER ||--o{ ORDER : "places"
    USER ||--o{ CART : "owns"
    USER ||--o{ WISHLIST : "has"
    USER ||--o{ USERADDRESS : "has"
    
    CATEGORY ||--o{ PRODUCT : "contains"
    PRODUCT ||--o{ ORDERITEM : "included_in"
    ORDER ||--|{ ORDERITEM : "contains"
    CART ||--o{ CARTITEM : "contains"
    PRODUCT ||--o{ CARTITEM : "added_to"
    
    FARMER ||--o{ PRODUCT : "manages"
    ORDER ||--|| FARMER : "fulfilled_by"
    
    CONTACT_US }|--|| USER : "submitted_by"
    CHATCONVERSATION }|--|| USER : "participates"
```

**Key Relationships:**
- Product belongs to Category (N:1)
- Order contains OrderItems (1:N)
- User has multiple Addresses (1:N)
- Farmer-User OneToOne

---

## 4. Class Diagram (Django Models)
**Key Classes with Attributes & Methods**

```mermaid
classDiagram
    class User {
        +id: int PK
        +username: str
        +email: str
        +is_staff: bool
        +authenticate()
        +login()
    }
    
    class Farmer {
        +id: int PK
        +user: User 1:1
        +name: str
        +phone: str
        +is_active: bool
        +create_product()
    }
    
    class Product {
        +id: int PK
        +name: str
        +price: Decimal
        +category: Category FK
        +farmer: Farmer FK
        +stock: int
        +image: ImageField
        +get_price()
        +update_stock()
    }
    
    class Category {
        +id: int PK
        +name: str
        +description: Text
        +products: List~Product~
    }
    
    class Order {
        +id: int PK
        +order_number: str
        +user: User FK
        +farmer: Farmer FK
        +total: Decimal
        +status: str
        +process_payment()
        +update_status()
    }
    
    class OrderItem {
        +id: int PK
        +order: Order FK
        +product: Product FK
        +quantity: int
        +calculate_subtotal()
    }
    
    User <|-- Farmer
    Category ||--o{ Product
    Farmer ||--o{ Product
    User ||--o{ Order
    Order ||--o{ OrderItem
    Product ||--o{ OrderItem
```

---

## 5. Sequence Diagrams

### 5.1 Customer Order Placement (Enhanced)
```mermaid
sequenceDiagram
    participant C as Customer
    participant UI as Frontend
    participant V as Django Views
    participant M as Models/DB
    participant P as Razorpay
    
    C->>UI: Add to Cart
    UI->>V: POST /cart/add/
    V->>M: CartItem.save()
    M-->>V: OK
    V-->>UI: Success
    
    C->>UI: Checkout
    UI->>V: POST /checkout/
    V->>M: Order.objects.create()
    V->>M: OrderItem.bulk_create()
    M-->>V: Order ID
    V->>P: create_order()
    P-->>V: Payment ID
    V-->>UI: Payment URL
    Note over C,P: Payment Success
    V->>M: order.update(status='confirmed')
```

### 5.2 Farmer Add Product
```mermaid
sequenceDiagram
    participant F as Farmer
    participant V as myadmin Views
    participant M as Models/DB
    
    F->>V: POST /farmers/products/add/
    V->>M: Product.objects.create(farmer=request.user.farmer)
    Note over V,M: Handle image upload to media/products/
    M-->>V: Product saved
    V-->>F: Success + redirect
```

### 5.3 Chatbot Interaction
```mermaid
sequenceDiagram
    participant U as User
    participant CB as Chatbot View
    participant CI as ChatIntelligence
    
    U->>CB: Send message
    CB->>CI: process_intent(message)
    CI-->>CB: Match intent + response
    CB->>M: ChatMessage.save()
    CB-->>U: Bot response + quick replies
```

---

## 6. Activity Diagrams

### 6.1 Customer Order Placement
```mermaid
flowchart TD
    A[Start: Browse Products] --> B[Search/Filter Category]
    B --> C{Add to Cart?}
    C -->|Yes| D[Update Cart]
    C -->|No| B
    D --> E[Proceed to Checkout?]
    E -->|No| B
    E -->|Yes| F[Enter Shipping Address]
    F --> G[Select Payment Method]
    G --> H[Process Payment]
    H --> I{Payment Success?}
    I -->|Yes| J[Order Confirmed<br/>Email Sent]
    I -->|No| K[Update Status: Failed]
    J --> L[End]
    K --> B
```

### 6.2 Admin Product Management
```mermaid
flowchart TD
    A[Admin Login] --> B[View Dashboard]
    B --> C{Action}
    C -->|View Products| D[List Products]
    C -->|Add Product| E[Product Form]
    C -->|Edit| F[Edit Form]
    C -->|Delete| G{Confirm Delete?}
    G -->|Yes| H[Delete from DB]
    G -->|No| D
    D --> C
    E --> I[Save Product<br/>Upload Image]
    F --> I
    I --> D
```

### 6.3 Farmer Registration
```mermaid
flowchart TD
    A[User Registration] --> B[Create User Account]
    B --> C[Set is_staff=True]
    C --> D[Create Farmer Profile]
    D --> E[Phone/Address Validation]
    E --> F{Valid?}
    F -->|Yes| G[Active Farmer<br/>Redirect to Dashboard]
    F -->|No| H[Show Errors]
    H --> D
```

**ASCII Backup for Activity (Order Flow):**
```
[Start] --> [View Products] --> [Add to Cart?] --No--> [Continue Browsing]
                          |
                       Yes
                          v
                    [Update Cart] --> [Checkout?] --No--> [Continue]
                                      |
                                    Yes
                                      v
                           [Enter Details] --> [Payment] --> [Success?] --No--> [Retry]
                                                                    |
                                                                  Yes
                                                                    v
                                                          [Order Confirmed] --> [End]
```

---

## Usage Notes
- **Mermaid Diagrams**: Copy to [Mermaid Live Editor](https://mermaid.live/) or GitHub README for interactive rendering.
- **Print-Ready**: Use Markdown viewer (VS Code, Typora) for report.
- **Based On**: Actual Django models from DATA_DICTIONARY.md and code structure.
- **Customization**: Edit this file directly for your presentation.

**Report Complete! All diagrams generated for BE Sem 8 submission.**
