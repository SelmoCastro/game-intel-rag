import os

from app.answer import AnswerAgent
from app.retriever import RetrievalService
from app.store import KnowledgeStore


def create_bot():
    import discord
    from discord import app_commands

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)
    agent = AnswerAgent(RetrievalService(KnowledgeStore()))

    @client.event
    async def on_ready():
        await tree.sync()
        print(f"Game Intel conectado como {client.user}")

    @tree.command(name="ask", description="Pergunta ao Game Intel")
    async def ask(interaction: discord.Interaction, pergunta: str):
        await interaction.response.defer()
        answer = agent.answer(pergunta, game="Hero Siege", season="Season 10")
        sources = "\n".join(f"- {source.title}: {source.url}" for source in answer.sources)
        message = answer.response
        if sources:
            message += f"\n\nFontes:\n{sources}"
        if answer.warning:
            message += f"\n\nAviso: {answer.warning}"
        await interaction.followup.send(message[:1900])

    return client


if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("DISCORD_BOT_TOKEN não configurado")
    create_bot().run(token)
