import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

TRADE_PROFILES = {
    "scalp":    {"sl": 0.5, "tp": 1.0},
    "intraday": {"sl": 1.0, "tp": 3.0},
    "swing":    {"sl": 2.0, "tp": 6.0},
}

PROFILE_COLORS = {
    "scalp":    discord.Color.blue(),
    "intraday": discord.Color.orange(),
    "swing":    discord.Color.purple(),
}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


DIRECTIONS = {"long", "short"}


@bot.command(name="r")
async def rr(ctx, *, raw: str = ""):
    parts = [p.strip() for p in raw.split(",")]

    if len(parts) not in (4, 5):
        await ctx.send(
            "**Usage:** `!r <entry>,<leverage>,<capital>,<type>[,<long|short>]`\n"
            "**Examples:**\n"
            "`!r 100000,10,60000,scalp`\n"
            "`!r 100000,10,60000,scalp,short`\n\n"
            "```\n"
            "scalp    — SL 0.5%  / TP 1.0%\n"
            "intraday — SL 1.0%  / TP 3.0%\n"
            "swing    — SL 2.0%  / TP 6.0%\n"
            "```"
            "_Direction defaults to long if omitted._"
        )
        return

    try:
        entry    = float(parts[0])
        leverage = float(parts[1])
        capital  = float(parts[2])
        ttype    = parts[3].lower()
    except ValueError:
        await ctx.send("❌ Entry, leverage, and capital must be numbers.")
        return

    direction = parts[4].lower() if len(parts) == 5 else "long"

    if entry <= 0 or leverage <= 0 or capital <= 0:
        await ctx.send("❌ Entry, leverage, and capital must be positive.")
        return

    if ttype not in TRADE_PROFILES:
        types = "`, `".join(TRADE_PROFILES)
        await ctx.send(f"❌ Unknown type. Use: `{types}`")
        return

    if direction not in DIRECTIONS:
        await ctx.send("❌ Direction must be `long` or `short`.")
        return

    sl_pct = TRADE_PROFILES[ttype]["sl"]
    tp_pct = TRADE_PROFILES[ttype]["tp"]
    position   = capital * leverage
    max_loss   = position * sl_pct / 100
    max_profit = position * tp_pct / 100
    rr_ratio   = tp_pct / sl_pct

    if direction == "long":
        sl_price = entry * (1 - sl_pct / 100)
        tp_price = entry * (1 + tp_pct / 100)
        direction_label = "📈  LONG"
    else:
        sl_price = entry * (1 + sl_pct / 100)
        tp_price = entry * (1 - tp_pct / 100)
        direction_label = "📉  SHORT"

    embed = discord.Embed(
        title=f"📊  {ttype.upper()}  {direction_label}  —  R:R  1:{rr_ratio:.1f}",
        color=PROFILE_COLORS[ttype],
    )

    embed.add_field(name="Entry",    value=f"${entry:,.2f}",   inline=True)
    embed.add_field(name="Leverage", value=f"{leverage:.0f}x", inline=True)
    embed.add_field(name="Capital",  value=f"${capital:,.2f}", inline=True)

    embed.add_field(name="​", value="​", inline=False)

    embed.add_field(
        name="🔴  Stop Loss",
        value=f"**${sl_price:,.2f}**\n`{'+' if direction == 'short' else '-'}{sl_pct}%`",
        inline=True,
    )
    embed.add_field(
        name="🟢  Take Profit",
        value=f"**${tp_price:,.2f}**\n`{'-' if direction == 'short' else '+'}{tp_pct}%`",
        inline=True,
    )

    embed.add_field(name="​", value="​", inline=False)

    embed.add_field(
        name="💸  Max Loss",
        value=f"`-${max_loss:,.2f}`",
        inline=True,
    )
    embed.add_field(
        name="💰  Max Profit",
        value=f"`+${max_profit:,.2f}`",
        inline=True,
    )

    embed.set_footer(
        text=f"Position: ${position:,.2f}  |  SL {sl_pct}% / TP {tp_pct}%"
    )

    await ctx.send(embed=embed)


@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖  RR Bot Help",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="!r <entry>,<leverage>,<capital>,<type>[,<direction>]",
        value=(
            "Calculate risk/reward for a trade.\n\n"
            "**Types:**\n"
            "`scalp` — SL 0.5% / TP 1.0%\n"
            "`intraday` — SL 1.0% / TP 3.0%\n"
            "`swing` — SL 2.0% / TP 6.0%\n\n"
            "**Direction:** `long` or `short` (default: `long`)\n\n"
            "**Examples:**\n"
            "`!r 100000,10,60000,scalp`\n"
            "`!r 100000,10,60000,swing,short`"
        ),
        inline=False,
    )
    await ctx.send(embed=embed)


token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN not set in .env")

bot.run(token)
