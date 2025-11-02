import graphene
from graphene_django import DjangoObjectType
from .models import Product


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'


class UpdatedProductType(graphene.ObjectType):
    """Type for updated product information"""
    id = graphene.ID()
    name = graphene.String()
    stock = graphene.Int()
    previous_stock = graphene.Int()


class UpdateLowStockProducts(graphene.Mutation):
    """
    Mutation to update products with low stock (stock < 10).
    Increments their stock by 10 to simulate restocking.
    """
    
    class Arguments:
        pass
    
    success = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(UpdatedProductType)
    
    def mutate(self, info):
        # Query products with stock < 10
        low_stock_products = Product.objects.filter(stock__lt=10)
        
        updated_products = []
        
        # Update each low-stock product
        for product in low_stock_products:
            previous_stock = product.stock
            product.stock += 10  # Increment stock by 10
            product.save()
            
            updated_products.append(UpdatedProductType(
                id=product.id,
                name=product.name,
                stock=product.stock,
                previous_stock=previous_stock
            ))
        
        if updated_products:
            message = f"Successfully restocked {len(updated_products)} low-stock products"
            success = True
        else:
            message = "No low-stock products found"
            success = True
        
        return UpdateLowStockProducts(
            success=success,
            message=message,
            updated_products=updated_products
        )


class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()


class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello from GraphQL!")
    
    # Add your other queries here
    products = graphene.List(ProductType)
    
    def resolve_products(self, info):
        return Product.objects.all()


schema = graphene.Schema(query=Query, mutation=Mutation)
