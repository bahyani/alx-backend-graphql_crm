# crm/schema.py

import graphene
from graphene_django import DjangoObjectType
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
import re
from .models import Customer, Product, Order
from crm.models import Product
from django.utils import timezone



# ==================== GraphQL Types ====================

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class UpdateLowStockProducts(graphene.Mutation):
    message = graphene.String()
    updated_products = graphene.List(ProductType)

    @classmethod
    def mutate(cls, root, info):
        low_stock_products = Product.objects.filter(stock__lt=10)

        updated = []
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated.append(product)

        return UpdateLowStockProducts(
            message=f"{len(updated)} products updated successfully",
            updated_products=updated
        )




class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# ==================== Input Types ====================

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# ==================== Utility Functions ====================

def validate_phone(phone):
    """
    Validate phone number format.
    Accepts: +1234567890, 123-456-7890, (123) 456-7890
    """
    if not phone:
        return True
    pattern = r'^(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}$'
    return bool(re.match(pattern, phone))


# ==================== Mutations ====================

class CreateCustomer(graphene.Mutation):
    """Create a single customer with validation."""

    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        try:
            # Validate email format
            validate_email(input.email)

            # Check if email already exists
            if Customer.objects.filter(email=input.email).exists():
                return CreateCustomer(
                    customer=None,
                    message="Email already exists",
                    success=False
                )

            # Validate phone format if provided
            if input.phone and not validate_phone(input.phone):
                return CreateCustomer(
                    customer=None,
                    message="Invalid phone format. Use +1234567890 or 123-456-7890",
                    success=False
                )

            # Create customer
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone if input.phone else None
            )

            return CreateCustomer(
                customer=customer,
                message="Customer created successfully",
                success=True
            )

        except ValidationError as e:
            return CreateCustomer(
                customer=None,
                message=f"Validation error: {str(e)}",
                success=False
            )
        except Exception as e:
            return CreateCustomer(
                customer=None,
                message=f"Error: {str(e)}",
                success=False
            )


class BulkCreateCustomers(graphene.Mutation):
    """Bulk create customers with partial success support."""

    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success = graphene.Boolean()

    def mutate(self, info, input):
        customers = []
        errors = []

        # Process each customer individually
        for idx, customer_data in enumerate(input):
            try:
                # Validate email format
                validate_email(customer_data.email)

                # Check if email already exists
                if Customer.objects.filter(email=customer_data.email).exists():
                    errors.append(f"Row {idx + 1}: Email {customer_data.email} already exists")
                    continue

                # Validate phone format if provided
                if customer_data.phone and not validate_phone(customer_data.phone):
                    errors.append(f"Row {idx + 1}: Invalid phone format for {customer_data.email}")
                    continue

                # Create customer
                customer = Customer.objects.create(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone if customer_data.phone else None
                )
                customers.append(customer)

            except ValidationError as e:
                errors.append(f"Row {idx + 1}: Validation error - {str(e)}")
            except Exception as e:
                errors.append(f"Row {idx + 1}: Error - {str(e)}")

        return BulkCreateCustomers(
            customers=customers,
            errors=errors if errors else None,
            success=len(customers) > 0
        )


class CreateProduct(graphene.Mutation):
    """Create a product with validation."""

    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        try:
            # Validate price is positive
            if input.price <= 0:
                return CreateProduct(
                    product=None,
                    message="Price must be positive",
                    success=False
                )

            # Validate stock is not negative
            stock = input.stock if input.stock is not None else 0
            if stock < 0:
                return CreateProduct(
                    product=None,
                    message="Stock cannot be negative",
                    success=False
                )

            # Create product
            product = Product.objects.create(
                name=input.name,
                price=input.price,
                stock=stock
            )

            return CreateProduct(
                product=product,
                message="Product created successfully",
                success=True
            )

        except Exception as e:
            return CreateProduct(
                product=None,
                message=f"Error: {str(e)}",
                success=False
            )


class CreateOrder(graphene.Mutation):
    """Create an order with customer and product associations."""

    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(pk=input.customer_id)
            except Customer.DoesNotExist:
                return CreateOrder(
                    order=None,
                    message=f"Customer with ID {input.customer_id} not found",
                    success=False
                )

            # Validate at least one product is provided
            if not input.product_ids or len(input.product_ids) == 0:
                return CreateOrder(
                    order=None,
                    message="At least one product must be selected",
                    success=False
                )

            # Validate all products exist
            products = []
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(pk=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    return CreateOrder(
                        order=None,
                        message=f"Invalid product ID: {product_id}",
                        success=False
                    )

            # Create order in a transaction
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    customer=customer,
                    order_date=input.order_date if hasattr(input, 'order_date') and input.order_date else None
                )

                # Associate products
                order.products.set(products)

                # Calculate total amount
                total = sum(product.price for product in products)
                order.total_amount = total
                order.save()

            return CreateOrder(
                order=order,
                message="Order created successfully",
                success=True
            )

        except Exception as e:
            return CreateOrder(
                order=None,
                message=f"Error: {str(e)}",
                success=False
            )


# ==================== Query Class ====================

class Query(graphene.ObjectType):
    """Root query for CRM."""

    hello = graphene.String(default_value="Hello, GraphQL!")

    # Single object queries
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    order = graphene.Field(OrderType, id=graphene.ID(required=True))

    # List queries
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            return None

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(pk=id)
        except Order.DoesNotExist:
            return None

    def resolve_all_customers(self, info):
        return Customer.objects.all()

    def resolve_all_products(self, info):
        return Product.objects.all()

    def resolve_all_orders(self, info):
        return Order.objects.all()


# ==================== Mutation Class ====================

class Mutation(graphene.ObjectType):
    """Root mutation for CRM."""

    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()


# ==================== Schema ====================

schema = graphene.Schema(query=Query, mutation=Mutation)