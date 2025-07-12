@bot.tree.command(name="creates", description="🎉 Boost / Invite plan server creator")
async def creates(interaction: discord.Interaction):
    # build the Select first
    class PlanSelect(discord.ui.Select):
        def __init__(self):
            opts = [
                discord.SelectOption(label="2× Boost (8 GB / 200 % / 30 GB)",  value="b2"),
                discord.SelectOption(label="4× Boost (14 GB / 300 % / 50 GB)",  value="b4"),
                discord.SelectOption(label="6× Boost (20 GB / 400 % / 70 GB)",  value="b6"),
                discord.SelectOption(label="Invite (14)  (12 GB)",             value="i14"),
                discord.SelectOption(label="Invite (19) (16 GB)",            value="i19"),
                discord.SelectOption(label="Invite (27+)  (20 GB)",             value="i27"),
            ]
            super().__init__(placeholder="Select a plan…", min_values=1, max_values=1, options=opts)

        async def callback(self, i2: discord.Interaction):
            plan = self.values[0]; m = i2.user; g = i2.guild
            # ---------- verification ----------
            allow = False
            if plan.startswith("b"):
                boost_needed = {"b2": 2, "b4": 4, "b6": 6}[plan]
                boost_count = sum(1 for r in m.roles if r.is_premium_subscriber())
                allow = boost_count >= boost_needed
                if not allow:
                    await i2.response.send_message(f"❌ Need {boost_needed} boosts; you have {boost_count}.", ephemeral=True)
                    return
            else:
                invites = await g.invites()
                uses = sum(inv.uses for inv in invites if inv.inviter and inv.inviter.id == m.id)
                needed = {"i5": 5, "i10": 10, "i20": 20}[plan]
                allow = uses >= needed
                if not allow:
                    await i2.response.send_message(f"❌ Need {needed}+ invites; you have {uses}.", ephemeral=True)
                    return

            await i2.response.send_message("⏳ Creating your server… check DM soon.", ephemeral=True)

            # ---------- resource table ----------
            conf = {
                "b2":  (8196, 200,  20796),
                "b4":  (14976, 300,  30755),
                "b6":  (20768, 400,  40965),
                "i14":  (12798, 200,  20796),
                "i10": (16768, 300,  30755),
                "i20": (20768, 400,  40965)
            }
            ram, cpu, disk = conf[plan]

            # ---------- background task ----------
            async def go():
                try:
                    await create_account_and_server(m, ram, cpu, disk)
                except Exception as e:
                    await m.send(f"❌ Internal error:\n```{e}```")
            asyncio.create_task(go())

    class V(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.add_item(PlanSelect())

    # send view immediately (NO defer first)
    await interaction.response.send_message("📦 **Choose your plan:**", view=V())

# -------------------- /multiple - Simple Multiplication Solver --------------------
@bot.tree.command(name="multiple", description="✖️ Multiply two numbers (admin + users)")
@app_commands.describe(a="First number", b="Second number")
async def multiple(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(f"{a} × {b} = **{a * b}**", ephemeral=True)

@bot.tree.command(name="controlpanel", description="⚙️  Quick panel menu")
async def controlpanel(interaction: discord.Interaction):
    class PanelView(discord.ui.View):
        @discord.ui.button(label="Create – Boost / Invite", style=discord.ButtonStyle.success)
        async def boost_invite(self, i: discord.Interaction, _):
            await i.response.send_message("Use **/creates** to open the Boost / Invite wizard.", ephemeral=True)

        @discord.ui.button(label="Create – Free 4 GB", style=discord.ButtonStyle.primary)
        async def free(self, i: discord.Interaction, _):
            await i.response.send_message('Run: `/createfree server‑name your@email.com`', ephemeral=True)

        @discord.ui.button(label="Panel URL", style=discord.ButtonStyle.gray)
        async def panel(self, i: discord.Interaction, _):
            await i.response.send_message(f"🌐 {PANEL_URL}", ephemeral=True)

    await interaction.response.send_message("Choose an option:", view=PanelView(), ephemeral=True)

@bot.tree.command(name="nodes", description="📊 Show node dashboard (public)")
async def nodes(interaction: discord.Interaction):
    await interaction.response.defer()                     # NOT ephemeral → visible to everyone
    headers = {"Authorization": f"Bearer {PANEL_API_KEY}", "Accept": "application/json"}

    async with aiohttp.ClientSession() as ses:
        # light request
        async with ses.get(f"{PANEL_URL}/api/application/nodes", headers=headers) as r:
            if r.status != 200:
                await interaction.followup.send("❌ Couldn’t contact panel.")
                return
            nodes = (await r.json())["data"]

    emb = discord.Embed(
        title="🗂️  Panel Node Dashboard",
        description=f"📡 Displaying status for **{len(nodes)}** nodes\n"
                    f"⏰ Last refreshed: <t:{int(datetime.datetime.utcnow().timestamp())}:R>",
        color=0x2ecc71
    )

    for node in nodes:
        a = node["attributes"]
        node_id = a["id"]
        status = "🟢 Online" if a["public"] else "🔴 Offline"

        # RAM / Disk
        used_m = a["allocated_resources"]["memory"]; tot_m = a["memory"]
        used_d = a["allocated_resources"]["disk"];   tot_d = a["disk"]

        emb.add_field(
            name=f"**{a['name']}**  (ID: {node_id})",
            value=(f"🛰 **Status:** {status}\n"
                   f"🌐 **FQDN:** {a['fqdn']} (Port 443)\n"
                   f"📦 **Memory:** {used_m:,} / {tot_m:,} MB\n"
                   f"💽 **Disk:** {used_d:,} / {tot_d:,} MB\n"
                   f"🔢 **Servers:** {a['allocated_resources']['servers']}"),
            inline=False
        )

    await interaction.followup.send(embed=emb)

@bot.tree.command(name="dm", description="✉️ DM any user (admin)")
@app_commands.describe(userid="Discord user ID", msg="Message")
async def dm(interaction: discord.Interaction, userid: str, msg: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        return
    try:
        u = await bot.fetch_user(int(userid))
        await u.send(msg)
        await interaction.response.send_message("✅ DM sent.")
    except Exception as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)

@bot.tree.command(name="ipcreate", description="🌐 Post server IP + ping user (admin)")
@app_commands.describe(ip="node1.godanime.net:25565", ping_user="UserID to ping")
async def ipcreate(interaction: discord.Interaction, ip: str, ping_user: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        return
    mention = f"<@{ping_user}>"
    await interaction.channel.send(f"🎮 **Your server IP:** `{ip}`\n{mention} PingYouMe")
    await interaction.response.send_message("✅ Sent.", ephemeral=True)

bot.run(TOKEN)
