
recipes = [
    {
        'name': 'Toasted Cheese Sandwich',
        'ingredients': ['Bread', 'Cheese'],
        'instructions': 'Use the toaster to make a delicious toasted cheese sandwich.'
    },
    {
        'name': 'Banana Bread',
        'ingredients': ['Banana', 'Bread'],
        'instructions': 'Make a classic banana bread by combining mashed bananas with bread and baking.'
    },
    {
        'name': 'Apple and Cheese Quesadilla',
        'ingredients': ['Apple', 'Cheese', 'Tortilla'],
        'instructions': 'Create a sweet and savory quesadilla by combining apple slices and cheese inside a tortilla, then cook until the cheese melts.'
    },
    {
        'name': 'Sweet Banana Smoothie',
        'ingredients': ['Banana', 'Sweet', 'Milk'],
        'instructions': 'Blend together banana, sweetener, and milk to make a sweet and creamy banana smoothie.'
    },
    {
        'name': 'Wine and Cheese Pairing',
        'ingredients': ['Cheese', 'Wine'],
        'instructions': 'Enjoy a sophisticated evening with a wine and cheese pairing. Explore different cheeses and wines to find complementary flavors.'
    },
    {
        'name': 'Cheese and Apple Snack Platter',
        'ingredients': ['Cheese', 'Apple', 'Sweet'],
        'instructions': 'Arrange slices of cheese and apple on a platter. Drizzle with honey or add a dollop of jam for a delightful snack.'
    },
    {
        'name': 'Milk and Cookie Time',
        'ingredients': ['Milk', 'Sweet (Cookies)'],
            'instructions': 'Dip your favorite cookies into a glass of milk for a classic and satisfying treat.'
    },
    {
        'name': 'Banana and Cheese Stuffed French Toast',
        'ingredients': ['Banana', 'Cheese', 'Bread', 'Milk', 'Sweet'],
        'instructions': 'Make a delicious stuffed French toast by filling it with a mixture of banana slices and cheese, then cooking until golden brown.'
    },
    {
        'name': 'Sweet Wine Cocktail',
        'ingredients': ['Wine', 'Sweet (Fruit Juice)'],
        'instructions': 'Create a sweet wine cocktail by mixing wine with your preferred sweet element. Garnish with fruit slices if available.'
    },
    {
        'name': 'Lollipop Garnished Cupcakes',
        'ingredients': ['Sweet (Lollipops)', 'Bread (Cupcake Base)'],
        'instructions': 'Decorate cupcakes with lollipops for a fun and colorful dessert.'
    },
    {
        'name': 'Cheese and Banana Stuffed Pancakes',
        'ingredients': ['Cheese', 'Banana', 'Flour', 'Milk'],
        'instructions': 'Prepare a pancake batter, stuff it with a mixture of cheese and banana slices, and cook until golden brown.'
    },
    {
        'name': 'Apple and Cheese Breakfast Muffins',
        'ingredients': ['Apple', 'Cheese', 'Flour', 'Milk', 'Sweet'],
        'instructions': 'Bake delicious breakfast muffins by combining diced apples and cheese in a sweet batter.'
    },
    {
        'name': 'Sweet Banana and Cheese Parfait',
        'ingredients': ['Banana', 'Cheese', 'Sweet', 'Yogurt'],
        'instructions': 'Create a delightful parfait by layering sweetened banana slices, cheese, and yogurt in a glass.'
    },
    {
        'name': 'Milk and Cheese Oatmeal',
        'ingredients': ['Milk', 'Cheese', 'Oats', 'Sweet'],
        'instructions': 'Cook a creamy oatmeal with milk and stir in grated cheese for a unique twist. Sweeten to taste.'
    },
    {
        'name': 'Wine-infused Cheese Fondue',
        'ingredients': ['Cheese', 'Wine', 'Bread'],
        'instructions': 'Prepare a classic cheese fondue by melting cheese with wine. Serve with bread cubes for dipping.'
    },
    {
        'name': 'Apple and Sweet Toasted Sandwich',
        'ingredients': ['Apple', 'Sweet', 'Bread', 'Cheese'],
        'instructions': 'Make a sweet and savory toasted sandwich with apple slices, sweet spread, and melted cheese.'
    },
    {
        'name': 'Banana and Cheese Roll-ups',
        'ingredients': ['Banana', 'Cheese', 'Tortilla', 'Sweet'],
        'instructions': 'Roll up banana slices and cheese in a tortilla, then drizzle with sweet sauce for a quick and tasty snack.'
    },
    {
        'name': 'Lollipop Milkshake',
        'ingredients': ['Sweet (Lollipops)', 'Milk', 'Sweet'],
        'instructions': 'Blend lollipops with milk and sweetener to create a colorful and fun lollipop milkshake.'
    },
    {
        'name': 'Cheese and Wine-infused Pasta',
        'ingredients': ['Cheese', 'Wine', 'Pasta', 'Sweet'],
        'instructions': 'Prepare a rich and flavorful pasta dish by combining cheese, wine, and a touch of sweetness.'
    },
]

# Feel free to customize or add more recipes as needed!

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import random, json

from .models import MarketUser, Product, Receipt
@permission_classes([IsAuthenticated])
class RecommendRecipesAPIView(APIView):
    def post(self, request):
        try:
            user = request.user
            ruser = MarketUser.objects.get(id=user.id)

            # Get all products from the user's receipts
            found,products_from_receipts = self.get_products_from_user_receipts(ruser)

            if not found:
                return Response({"success": False, "message": "User has no receipts"})

            # Combine product descriptions from all products and products from user's receipts
            all_products = Product.objects.all()
            all_product_descriptions = [product.desc for product in all_products] + products_from_receipts

            # Use TfidfVectorizer to convert product descriptions into numerical representations
            vectorizer = TfidfVectorizer(stop_words='english')
            product_matrix = vectorizer.fit_transform(all_product_descriptions)

            # Calculate similarity between products based on descriptions
            cosine_similarities = linear_kernel(product_matrix, product_matrix)

            # Recommendations for the first product in the list (modify as needed)
            product_index = 0
            similar_products_indices = cosine_similarities[product_index].argsort()[::-1][1:6]  # Exclude the product itself

            # Retrieve recommended product names
            recommended_product_names = [all_products[int(index)].name for index in similar_products_indices if 0 <= int(index) < len(all_products)]


            # Include recommended recipes in the response
            recommended_recipes = self.get_recommended_recipes(recommended_product_names)
            return Response({
                "success": True,
                'message': "Recipes Recommended",
                'recommended_recipes': recommended_recipes,
            })

        except MarketUser.DoesNotExist:
            return Response({"success": False, "message": f"User not found"})
    def get_products_from_user_receipts(self, user):
        # Retrieve products from user's receipts (modify as needed based on your model structure)
        user_receipts = Receipt.objects.filter(user=user)
        if not user_receipts:
            return False,[]
        
        # Get the item IDs from the receipts
        item_ids = [item['item'] for receipt in user_receipts for item in json.loads(receipt.products)]
        
        # Fetch product descriptions from the Product model
        products = Product.objects.filter(id__in=item_ids)
        product_descriptions = [product.desc for product in products]
        
        return True,product_descriptions


    def get_recommended_recipes(self, recommended_product_names):
        # Directly use the provided recipes array and filter by matching ingredients
        matching_recipes = [recipe for recipe in recipes if any(ingredient.lower() in recommended_product_names for ingredient in recipe['ingredients'])]

        # Select a random recipe from the matching ones
        if matching_recipes:
            return random.choice(matching_recipes)
        else:
            return {}  # Return an empty object if there are no matching recipes
