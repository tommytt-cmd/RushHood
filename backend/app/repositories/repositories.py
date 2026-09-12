from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Bet, Player, Round

class PlayerRepository:
  def __init__(self,s:AsyncSession): self.s=s
  async def get_or_create(self,wallet:str)->Player:
    p=await self.s.scalar(select(Player).where(Player.wallet_address==wallet.lower()))
    if not p: p=Player(wallet_address=wallet.lower()); self.s.add(p); await self.s.flush()
    return p
class RoundRepository:
  def __init__(self,s:AsyncSession): self.s=s
  async def current(self): return await self.s.scalar(select(Round).order_by(Round.created_at.desc()))
  async def get(self,id:UUID): return await self.s.get(Round,id)
   async def add(self,r:Round): self.s.add(r); await self.s.flush(); return r
class BetRepository:
  def __init__(self,s:AsyncSession): self.s=s
  async def exists(self,r:UUID,p:UUID): return await self.s.scalar(select(Bet.id).where(Bet.round_id==r,Bet.player_id==p)) is not None
  async def add(self,b:Bet): self.s.add(b); await self.s.flush(); return b
  async def by_round(self,r:UUID): return list((await self.s.scalars(select(Bet).where(Bet.round_id==r))).all())
  async def by_wallet(self,w:str): return list((await self.s.scalars(select(Bet).join(Player).where(Player.wallet_address==w.lower()).order_by(Bet.created_at.desc()))).all())
