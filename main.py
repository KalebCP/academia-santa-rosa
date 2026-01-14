import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
# ================= CONFIG =================
POLICIA_ROLES = [
    1447372606117515294,
    1447372607442653235,
    1447373579501965493
]

# ROLES DE ADMINISTRADOR/OWNERS
ADMIN_ROLE = [
    1447363783033884733,
    1446951116502994955,
    1446951159553065063
]
def es_admin(member: discord.Member) -> bool:
    return any(role.id in ADMIN_ROLE for role in member.roles)

ROL_CIUDADANO = 1447360405726040166  # 👈 ID del rol Ciudadano

LOGS_CANAL = 1454868672974688430  # ID canal logs multas

MULTAS_FILE = "multas.json"
ANTECEDENTES_FILE = "antecedentes.json"

# CONFIG UNBELIEVA
UNBELIEVA_API_KEY = os.getenv ("UMBELIEVA_API_KEY")
UNBELIEVA_GUILD_ID = int(os.getenv("UNBELIEVA_GUILD_ID"))  # ID del servidor Discord
UNBELIEVA_HEADERS = {
    "Authorization": UNBELIEVA_API_KEY,
    "Content-Type": "application/json"
}


# ================= BOT =================
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= JSON =================
def cargar_json(archivo):
    if not os.path.exists(archivo) or os.path.getsize(archivo) == 0:
        return {}
    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_json(archivo, data):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

antecedentes = cargar_json(ANTECEDENTES_FILE)
multas = cargar_json(MULTAS_FILE)

# ================= PERMISOS =================
def es_policia_o_admin(member: discord.Member):
    roles = [r.id for r in member.roles]
    return any(r in roles for r in ADMIN_ROLE) or any(r in roles for r in POLICIA_ROLES)

# ================= ROBLOX AVATAR =================
def obtener_avatar_roblox(username):
    try:
        r = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [username]}
        ).json()
        user_id = r["data"][0]["id"]

        thumb = requests.get(
            f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
        ).json()

        return thumb["data"][0]["imageUrl"]
    except:
        return None

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Conectado como {bot.user}")

# ================= MULTA AGREGAR =================
@bot.tree.command(name="multa-agregar", description="Agregar multa de tránsito")
async def multa_agregar(
    interaction: discord.Interaction,
    usuario: discord.Member,
    roblox_user: str,
    articulos: str,
    monto: int,
    matricula: str,
    oficial: str,
    prueba: discord.Attachment = None
):
    if not es_policia_o_admin(interaction.user):
        await interaction.response.send_message("❌ Sin permisos.", ephemeral=True)
        return

    await interaction.response.defer()

    uid = str(usuario.id)
    multas.setdefault(uid, [])

    multa_id = len(multas[uid]) + 1
    avatar = obtener_avatar_roblox(roblox_user)

    multas[uid].append({
        "id": multa_id,
        "articulos": articulos,
        "monto": monto,
        "oficial": oficial,
        "matricula": matricula,
        "roblox": roblox_user,
        "avatar": avatar,
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "estado": "PENDIENTE",
        "prueba": prueba.url if prueba else None
    })

    guardar_json(MULTAS_FILE, multas)

    embed = discord.Embed(
        title="🚨 Registro de Infracción de Tránsito",
        color=discord.Color.red()
    )

    embed.add_field(name="👮 Oficial a cargo", value=oficial, inline=True)
    embed.add_field(name="👤 Infractor", value=usuario.mention, inline=True)
    embed.add_field(name="📄 Artículos infringidos", value=articulos, inline=False)
    embed.add_field(name="💰 Monto de la multa", value=f"${monto} USD", inline=True)
    embed.add_field(name="🚗 Matrícula", value=matricula, inline=True)
    embed.add_field(name="📅 Fecha", value=datetime.now().strftime("%d/%m/%Y"), inline=True)

    if avatar:
        embed.set_thumbnail(url=avatar)

    if prueba:
        embed.set_image(url=prueba.url)

    embed.set_footer(text="[NYC:RP] New York City Roleplay")

    await interaction.followup.send(embed=embed)

# ================= VER MULTAS CON PAGINAS (ESTRUCTURA) =================

# VIEW DE MULTAS
class MultasView(discord.ui.View):
    def __init__(self, interaction, multas, propietario):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.multas = multas
        self.propietario = propietario
        self.index = 0

    # EMBED DINÁMICO
    def crear_embed(self):
        m = self.multas[self.index]

        embed = discord.Embed(
            title=f"🚓 MULTA #{m['id']} — {m['estado']}",
            color=discord.Color.red() if m["estado"] == "PENDIENTE" else discord.Color.green()
        )

        embed.add_field(name="👮 Oficial", value=m["oficial"], inline=True)
        embed.add_field(name="💰 Monto", value=f"${m['monto']}", inline=True)
        embed.add_field(name="🚗 Matrícula", value=m["matricula"], inline=True)
        embed.add_field(name="📄 Artículos", value=m["articulos"], inline=False)
        embed.add_field(name="📅 Fecha", value=m["fecha"], inline=True)

        embed.set_footer(text=f"Multa {self.index + 1} de {len(self.multas)}")

        if m.get("avatar"):
            embed.set_thumbnail(url=m["avatar"])

        if m.get("prueba"):
            embed.set_image(url=m["prueba"])

        return embed

# BOTONES
class MultasView(discord.ui.View):
    def __init__(self, interaction, multas, propietario):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.multas = multas
        self.propietario = propietario
        self.index = 0

    def crear_embed(self):
        m = self.multas[self.index]

        embed = discord.Embed(
            title=f"🚓 MULTA #{m['id']} — {m['estado']}",
            color=discord.Color.red() if m["estado"] == "PENDIENTE" else discord.Color.green()
        )

        embed.add_field(name="👮 Oficial", value=m["oficial"], inline=True)
        embed.add_field(name="💰 Monto", value=f"${m['monto']}", inline=True)
        embed.add_field(name="🚗 Matrícula", value=m["matricula"], inline=True)
        embed.add_field(name="📄 Artículos", value=m["articulos"], inline=False)
        embed.add_field(name="📅 Fecha", value=m["fecha"], inline=True)

        embed.set_footer(text=f"Multa {self.index + 1} de {len(self.multas)}")

        if m.get("avatar"):
            embed.set_thumbnail(url=m["avatar"])

        if m.get("prueba"):
            embed.set_image(url=m["prueba"])

        return embed

    # ⬅️ BOTÓN ANTERIOR
    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message(
                "❌ No es tu multa.", ephemeral=True
            )

        if self.index > 0:
            self.index -= 1

        await interaction.response.edit_message(
            embed=self.crear_embed(),
            view=self
        )

    # ➡️ BOTÓN SIGUIENTE
    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message(
                "❌ No es tu multa.", ephemeral=True
            )

        if self.index < len(self.multas) - 1:
            self.index += 1

        await interaction.response.edit_message(
            embed=self.crear_embed(),
            view=self
        )

    # 💰 BOTÓN PAGAR
    @discord.ui.button(label="Pagar multa", style=discord.ButtonStyle.success, emoji="💰")
    async def pagar(self, interaction: discord.Interaction, button: discord.ui.Button):
        multa = self.multas[self.index]

        if interaction.user.id != self.propietario:
            return await interaction.response.send_message(
                "❌ No es tu multa.", ephemeral=True
            )

        if multa["estado"] != "PENDIENTE":
            return await interaction.response.send_message(
                "❌ Esta multa no se puede pagar.", ephemeral=True
            )

        # (Luego conectas UnbelievaBoat aquí)
        multa["estado"] = "PAGADA"
        guardar_json(MULTAS_FILE, multas)

        await interaction.response.edit_message(
            embed=self.crear_embed(),
            view=self
        )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        await self.interaction.edit_original_response(view=self)

# ================= VER MULTAS =================
@bot.tree.command(name="multas", description="Ver multas")
async def ver_multas(interaction: discord.Interaction, usuario: discord.Member | None = None):
    target = usuario or interaction.user

    if usuario and not es_policia_o_admin(interaction.user):
        return await interaction.response.send_message("❌ Sin permisos.", ephemeral=True)

    uid = str(target.id)

    if uid not in multas or not multas[uid]:
        return await interaction.response.send_message("✅ No tienes multas.")

    view = MultasView(interaction, multas[uid], target.id)
    embed = view.crear_embed()

    await interaction.response.send_message(embed=embed, view=view)

# ================= FUNCIONES DE ECONOMIA (PAGAR MULTAS) =================

# OBTENER BALANCE
def obtener_balance(user_id: int):
    url = f"https://unbelievaboat.com/api/v1/guilds/{UNBELIEVA_GUILD_ID}/users/{user_id}"
    r = requests.get(url, headers=UNBELIEVA_HEADERS)

    if r.status_code != 200:
        return None

    return r.json()["cash"]

# QUITAR DINERO
def quitar_dinero(user_id: int, monto: int, razon="Pago de multa"):
    url = f"https://unbelievaboat.com/api/v1/guilds/{UNBELIEVA_GUILD_ID}/users/{user_id}"

    data = {
        "cash": -monto,
        "reason": razon
    }

    r = requests.patch(url, headers=UNBELIEVA_HEADERS, json=data)
    return r.status_code == 200

# ================= PAGAR MULTA =================
@bot.tree.command(name="pagar-multa", description="Pagar una multa con tu dinero")
async def pagar_multa(interaction: discord.Interaction, id_multa: int):
    uid = str(interaction.user.id)
    user_id = interaction.user.id

    if uid not in multas:
        await interaction.response.send_message(
            "❌ No tienes multas.",
            ephemeral=True
        )
        return

    for m in multas[uid]:
        if m["id"] == id_multa:
            if m["estado"] == "PAGADA":
                await interaction.response.send_message(
                    "✅ Esta multa ya está pagada.",
                    ephemeral=True
                )
                return

            balance = obtener_balance(user_id)

            if balance is None:
                await interaction.response.send_message(
                    "❌ Error al verificar tu dinero.",
                    ephemeral=True
                )
                return

            if balance < m["monto"]:
                await interaction.response.send_message(
                    f"❌ No tienes suficiente dinero.\n💰 Balance: ${balance}",
                    ephemeral=True
                )
                return

            if not quitar_dinero(user_id, m["monto"]):
                await interaction.response.send_message(
                    "❌ Error al procesar el pago.",
                    ephemeral=True
                )
                return

            m["estado"] = "PAGADA"
            guardar_json(MULTAS_FILE, multas)

            await interaction.response.send_message(
                f"✅ Multa #{id_multa} pagada correctamente.\n💰 -${m['monto']}",
                ephemeral=True
            )
            return

    await interaction.response.send_message(
        "❌ Multa no encontrada.",
        ephemeral=True
    )
# ================= ELIMINAR MULTA =================
@bot.tree.command(name="eliminar-multa", description="Eliminar multa")
async def eliminar_multa(
    interaction: discord.Interaction,
    usuario: discord.Member,
    id_multa: int
):
    if not es_policia_o_admin(interaction.user):
        await interaction.response.send_message("❌ Sin permisos.", ephemeral=True)
        return

    uid = str(usuario.id)

    for m in multas.get(uid, []):
        if m["id"] == id_multa:
            multas[uid].remove(m)
            guardar_json(MULTAS_FILE, multas)
            await interaction.response.send_message("🗑️ Multa eliminada.")
            return

    await interaction.response.send_message("❌ Multa no encontrada.", ephemeral=True)

# ================= ANTECEDENTE AGREGAR =================
from datetime import datetime, timedelta

@bot.tree.command(name="antecedente-agregar", description="Agregar arresto / antecedente policial")
async def antecedente_agregar(
    interaction: discord.Interaction,
    usuario: discord.User,
    roblox_user: str,
    articulos: str,
    descripcion: str,
    minutos_arresto: int,
    oficial: str,
    prueba: discord.Attachment | None = None
):
    if not es_policia_o_admin(interaction.user):
        await interaction.response.send_message("❌ Sin permisos.", ephemeral=True)
        return

    await interaction.response.defer()

    uid = str(usuario.id)
    antecedentes.setdefault(uid, [])

    ant_id = len(antecedentes[uid]) + 1

    fecha_arresto = datetime.now()
    fecha_liberacion = fecha_arresto + timedelta(minutes=minutos_arresto)

    avatar = obtener_avatar_roblox(roblox_user)

    antecedentes[uid].append({
        "id": ant_id,
        "roblox": roblox_user,
        "articulos": articulos,
        "descripcion": descripcion,
        "oficial": oficial,
        "tiempo": minutos_arresto,
        "fecha_arresto": fecha_arresto.strftime("%d/%m/%Y %H:%M"),
        "fecha_liberacion": fecha_liberacion.strftime("%d/%m/%Y %H:%M"),
        "avatar": avatar,
        "prueba": prueba.url if prueba else None
    })

    guardar_json(ANTECEDENTES_FILE, antecedentes)

    embed = discord.Embed(
        title=f"📂 Antecedente #{ant_id} registrado",
        color=discord.Color.dark_red()
    )

    embed.add_field(name="Usuario", value=usuario.mention, inline=False)
    embed.add_field(name="Artículos", value=articulos, inline=False)
    embed.add_field(name="Descripción", value=descripcion, inline=False)
    embed.add_field(name="Oficial", value=oficial, inline=True)
    embed.add_field(name="Tiempo", value=f"{minutos_arresto} minutos", inline=True)
    embed.add_field(
        name="Fecha arresto",
        value=fecha_arresto.strftime("%d/%m/%Y %H:%M"),
        inline=True
    )
    embed.add_field(
        name="Fecha liberación",
        value=fecha_liberacion.strftime("%d/%m/%Y %H:%M"),
        inline=True
    )

    if avatar:
        embed.set_thumbnail(url=avatar)

    if prueba:
        embed.set_image(url=prueba.url)

    await interaction.followup.send(embed=embed, ephemeral=True)

# ================= VIEW CON BOTONES =================
class AntecedentesView(discord.ui.View):
    def __init__(self, interaction, target, antecedentes):
        super().__init__(timeout=300)
        self.interaction = interaction
        self.target = target
        self.antecedentes = antecedentes
        self.index = 0

    def crear_embed(self):
        a = self.antecedentes[self.index]

        embed = discord.Embed(
            title=f"📂 ANTECEDENTE #{a['id']}",
            description=f"Sujeto: {self.target.mention}",
            color=discord.Color.dark_red()
        )

        embed.add_field(name="📄 Artículos", value=a["articulos"], inline=False)
        embed.add_field(name="📝 Descripción", value=a["descripcion"], inline=False)
        embed.add_field(name="👮 Oficial", value=a["oficial"], inline=True)
        embed.add_field(name="⏱ Tiempo", value=f"{a['tiempo']} minutos", inline=True)
        embed.add_field(name="📅 Arresto", value=a["fecha_arresto"], inline=True)
        embed.add_field(name="📅 Liberación", value=a["fecha_liberacion"], inline=True)

        if a.get("avatar"):
            embed.set_thumbnail(url=a["avatar"])

        if a.get("prueba"):
            embed.set_image(url=a["prueba"])

        embed.set_footer(text=f"Página {self.index+1}/{len(self.antecedentes)}")
        return embed

    # ⬅️ BOTÓN ANTERIOR
    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message(
                "❌ No puedes usar estos botones.", ephemeral=True
            )
            return

        if self.index > 0:
            self.index -= 1

        await interaction.response.edit_message(
            embed=self.crear_embed(),
            view=self
        )

    # ➡️ BOTÓN SIGUIENTE
    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message(
                "❌ No puedes usar estos botones.", ephemeral=True
            )
            return

        if self.index < len(self.antecedentes) - 1:
            self.index += 1

        await interaction.response.edit_message(
            embed=self.crear_embed(),
            view=self
        )

    # ⏳ EXPIRACIÓN
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        await self.interaction.edit_original_response(view=self)

# ================= ANTECEDENTES =================
@bot.tree.command(name="antecedentes", description="Ver antecedentes policiales")
async def ver_antecedentes(
    interaction: discord.Interaction,
    usuario: discord.User | None = None
):
    target = usuario or interaction.user

    if usuario and not es_policia_o_admin(interaction.user):
        await interaction.response.send_message("❌ Sin permisos.", ephemeral=True)
        return

    uid = str(target.id)

    if uid not in antecedentes or not antecedentes[uid]:
        await interaction.response.send_message("✅ Sin antecedentes registrados.", ephemeral=True)
        return

    view = AntecedentesView(interaction, target, antecedentes[uid])
    embed = view.crear_embed()

    await interaction.response.send_message(
        embed=embed,
        view=view
    )

# ================= ELIMINAR ANTECEDENTES =================
@bot.tree.command(name="eliminar-antecedente", description="Eliminar antecedente")
async def eliminar_antecedente(
    interaction: discord.Interaction,
    usuario: discord.User,
    id_antecedente: int
):
    if not es_policia_o_admin(interaction.user):
        await interaction.response.send_message("❌ Sin permisos.", ephemeral=True)
        return

    uid = str(usuario.id)

    for a in antecedentes.get(uid, []):
        if a["id"] == id_antecedente:
            antecedentes[uid].remove(a)
            guardar_json(ANTECEDENTES_FILE, antecedentes)
            await interaction.response.send_message("🗑️ Antecedente eliminado.")
            return

    await interaction.response.send_message("❌ Antecedente no encontrado.", ephemeral=True)


    # ================= RUN =================
bot.run(TOKEN)