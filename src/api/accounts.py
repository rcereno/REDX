import sqlalchemy
from src.api import database as db

from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(auth.get_api_key)],
)

class Account(BaseModel):
    customer_name: str
    customer_email: str

@router.post("/{customer_id}/register")
def register_customer(customer: Account):
    """ """
    with db.engine.begin() as connection:       
        connection.execute(
            sqlalchemy.text(
                "INSERT INTO accounts (email, name) VALUES (:name, :email)"
            ),
            {"name": customer.customer_name, "email": customer.customer_email}
        )
    
    return "OK"

@router.post("/{account_id}/view")
def account_view(account_id: int):
    """
    """

    with db.engine.begin() as connection: 
        name = connection.execute(
            sqlalchemy.text(
                """
                SELECT name
                FROM accounts 
                WHERE id = :account_id
                LIMIT 1
                """
            ),
            [{
                "account_id": account_id
            }]
        ).scalar_one()

        games_owned = connection.execute(
            sqlalchemy.text(
                """
                SELECT games.name
                FROM purchases
                JOIN games
                ON games.id = purchases.game_id
                WHERE purchases.account_id = :account_id
                ORDER BY play_time DESC
                """
            ),
            [{
                "account_id": account_id
            }]
        ).fetchall()

        wishlist = connection.execute(
            sqlalchemy.text(
                """
                SELECT games.name
                FROM wishlisted
                JOIN games
                ON games.id = wishlisted.game_id
                WHERE wishlisted.account_id = :account_id
                """
            ),
            [{
                "account_id": account_id
            }]
        ).fetchall()
        # fetch most recent cart they have (should only have one)
        current_cart_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT id FROM carts
                WHERE carts.account_id = :account_id
                ORDER BY created_at DESC
                """
            ),
             [{
                "account_id": account_id
            }]
        ).scalar_one()
        cart_items_results = connection.execute(
            sqlalchemy.text(
                """
                SELECT COUNT(game_id), SUM(cost)
                FROM cart_items
                WHERE cart_items.cart_id = :cart_id
                """
            ),
             [{
                "cart_id": current_cart_id
            }]
        ).fetchone()
        games_in_cart, cost = cart_items_results

        return {
            "customer_name": name,
            "games_owned": games_owned,
            "wishlist": wishlist,
            "current_cart": f"Games in cart: {games_in_cart}, Cost: {cost}"
        } 

class Review(BaseModel):
    rating: int


@router.post("/{account_id}/reviews/{game_sku}")
def add_review(account_id: int, game_sku: int, review: Review):
    """ """

    with db.engine.begin() as connection:
        game_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT id
                FROM games 
                WHERE item_sku = :sku
                """
            ),
            [{
                "sku": game_sku
            }]
        ).scalar_one()
        purchased = connection.execute(
            sqlalchemy.text(
                """
                SELECT account_id, game_id
                FROM purchased
                WHERE account_id = :acc_id
                AND game_Id = :game_id
                """
            ),
            {
                "acc_id": account_id,
                "game_id": game_id
            }
        ).fetchone()
        if purchased:
            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO reviews (account_id, game_id, review)
                    VALUES (:account_id, :game_id, :review)
                    ON DUPLICATE KEY UPDATE review = VALUES(:review)
                    """
                ),
                [{
                    "account_id": account_id,
                    "game_id": game_id,
                    "review": review.rating
                }]
            )
        else:
            return "Cannot review a game you do not own."
            
    return "OK"

