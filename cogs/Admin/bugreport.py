import discord
from discord.ext import commands
import json
from datetime import datetime
import os
import asyncio
from github import Github

class BugReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bug_reports_file = ".json/bug_reports.json"
        self.report_receiver_id = 110927272210354176
        if not os.path.exists(self.bug_reports_file):
            with open(self.bug_reports_file, "w") as f:
                json.dump([], f)

    class BugReportButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Report Bug", style=discord.ButtonStyle.red, emoji="🐛")
        async def bug_report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            modal = BugReport.BugReportModal()
            await interaction.response.send_modal(modal)

    class BugReportModal(discord.ui.Modal, title="Bug Report"):
        bug_title = discord.ui.TextInput(
            label="Bug Title",
            placeholder="Enter a brief title for the bug",
            required=True,
            max_length=100
        )

        bug_description = discord.ui.TextInput(
            label="Bug Description",
            placeholder="Describe the bug in detail",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=1000
        )

        steps_to_reproduce = discord.ui.TextInput(
            label="Steps to Reproduce",
            placeholder="List the steps to reproduce this bug",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=1000
        )

        async def on_submit(self, interaction: discord.Interaction):
            bug_report = {
                "report_id": str(len(self.get_all_reports()) + 1),
                "author_id": interaction.user.id,
                "author_name": str(interaction.user),
                "title": str(self.bug_title),
                "description": str(self.bug_description),
                "steps": str(self.steps_to_reproduce),
                "timestamp": datetime.now().isoformat(),
                "status": "Open"
            }

            self.save_report(bug_report)

            embed = discord.Embed(
                title="New Bug Report",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Report ID", value=bug_report["report_id"], inline=False)
            embed.add_field(name="Reported By", value=f"{bug_report['author_name']} (ID: {bug_report['author_id']})", inline=False)
            embed.add_field(name="Title", value=bug_report["title"], inline=False)
            embed.add_field(name="Description", value=bug_report["description"], inline=False)
            embed.add_field(name="Steps to Reproduce", value=bug_report["steps"], inline=False)

            cog = interaction.client.get_cog("BugReport")
            try:
                receiver = await interaction.client.fetch_user(cog.report_receiver_id)
                await receiver.send(embed=embed)
            except discord.HTTPException as e:
                print(f"Failed to send DM: {e}")

            await interaction.response.send_message(
                "Bug report submitted successfully! Thank you for your report.", 
                ephemeral=True, delete_after=8
            )

        def get_all_reports(self):
            try:
                with open(".json/bug_reports.json", "r") as f:
                    return json.load(f)
            except:
                return []

        def save_report(self, report):
            reports = self.get_all_reports()
            reports.append(report)
            with open(".json/bug_reports.json", "w") as f:
                json.dump(reports, f, indent=4)

    class BugReportPaginator(discord.ui.View):
        def __init__(self, reports, current_page=0):
            super().__init__(timeout=60)
            self.reports = reports
            self.current_page = current_page
            self.max_pages = len(reports)
            self.github = Github(os.getenv('GITHUB_TOKEN'))
            self.repo_name = "xyz-q/Python-Bot"
            
        @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
        async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.current_page = max(0, self.current_page - 1)
            await self.update_message(interaction)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.current_page = min(self.max_pages - 1, self.current_page + 1)
            await self.update_message(interaction)

        @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
        async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                report = self.reports[self.current_page]
                
                # Create GitHub issue
                try:
                    repo = self.github.get_repo(self.repo_name)
                    issue_title = f"Bug Report: {report['title']}"
                    issue_body = (
                        f"**Reporter:** {report['author_name']}\n"
                        f"**Description:**\n{report['description']}\n\n"
                        f"**Steps to Reproduce:**\n{report['steps']}\n\n"
                        f"**Date Reported:** {report['timestamp']}\n"
                        f"**Discord User ID:** {report['author_id']}"
                    )
                    issue = repo.create_issue(title=issue_title, body=issue_body, labels=['bug'])
                    
                    # Update notification embed to include issue link
                    notification_embed = discord.Embed(
                        title=f"Bug Report #{report['report_id']} Accepted",
                        description=(
                            f"Your bug report '{report['title']}' has been accepted and will be worked on.\n"
                            f"GitHub Issue: {issue.html_url}\n"
                            f"Thank you for your help <3"
                        ),
                        color=discord.Color.green()
                    )
                except Exception as e:
                    print(f"Failed to create GitHub issue: {e}")
                    # Fall back to original notification if GitHub creation fails
                    notification_embed = discord.Embed(
                        title=f"Bug Report #{report['report_id']} Accepted",
                        description=f"Your bug report '{report['title']}' has been accepted and will be worked on.\nThank you for your help <3",
                        color=discord.Color.green()
                    )

                # Rest of your existing accept_button code...
                try:
                    user = await interaction.client.fetch_user(report['author_id'])
                    await user.send(embed=notification_embed)
                except discord.HTTPException:
                    print(f"Could not DM user {report['author_name']}")

                # Update the JSON file
                with open(".json/bug_reports.json", "r") as f:
                    all_reports = json.load(f)

                all_reports = [r for r in all_reports if r['report_id'] != report['report_id']]
                
                with open(".json/bug_reports.json", "w") as f:
                    json.dump(all_reports, f, indent=4)

                # Update the view
                self.reports = all_reports
                self.max_pages = len(all_reports)

                if not all_reports:
                    await interaction.message.delete()
                    await interaction.response.send_message("All bug reports have been handled!", ephemeral=True, delete_after=8)
                    return

                if self.current_page >= len(all_reports):
                    self.current_page = len(all_reports) - 1

                # Update to next report
                next_report = all_reports[self.current_page]
                new_embed = discord.Embed(
                    title=f"Bug Report #{next_report['report_id']}",
                    description=f"**Title:** {next_report['title']}\n\n"
                            f"**Description:** {next_report['description']}\n\n"
                            f"**Steps to Reproduce:** {next_report['steps']}\n\n"
                            f"**Reported by:** {next_report['author_name']}\n"
                            f"**Status:** {next_report.get('status', 'Open')}\n"
                            f"**Date:** {next_report['timestamp']}",
                    color=discord.Color.red()
                )
                new_embed.set_footer(text=f"Page {self.current_page + 1}/{len(all_reports)}")

                await interaction.response.edit_message(embed=new_embed, view=self)

            except Exception as e:
                print(f"Error in accept_button: {e}")
                await interaction.response.send_message("An error occurred while processing the report.", ephemeral=True, delete_after=8)



        @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
        async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.message.delete()

        async def save_and_notify(self, interaction, report, action):
            with open(".json/bug_reports.json", "r") as f:
                all_reports = json.load(f)
            
            for r in all_reports:
                if r['report_id'] == report['report_id']:
                    r['status'] = report['status']
                    break
            
            with open(".json/bug_reports.json", "w") as f:
                json.dump(all_reports, f, indent=4)

            notification_embed = discord.Embed(
                title=f"Bug Report #{report['report_id']} {action.title()}",
                description=f"Your bug report '{report['title']}' has been {action}.",
                color=discord.Color.gold()
            )

            try:
                user = await interaction.client.fetch_user(report['author_id'])
                await user.send(embed=notification_embed)
            except discord.HTTPException:
                print(f"Could not DM user {report['author_name']}")

            await self.update_message(interaction)

        async def update_message(self, interaction):
            report = self.reports[self.current_page]
            
            color = discord.Color.red()
            if report['status'] == "Accepted":
                color = discord.Color.green()
            elif report['status'] == "Declined":
                color = discord.Color.red()
            elif report['status'] == "Closed":
                color = discord.Color.light_grey()

            embed = discord.Embed(
                title=f"Bug Report #{report['report_id']}",
                description=f"**Title:** {report['title']}\n\n"
                        f"**Description:** {report['description']}\n\n"
                        f"**Steps to Reproduce:** {report['steps']}\n\n"
                        f"**Reported by:** {report['author_name']}\n"
                        f"**Status:** {report['status']}\n"
                        f"**Date:** {report['timestamp']}",
                color=color
            )
            embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}")
            await interaction.response.edit_message(embed=embed, view=self)


    @commands.command(name="bugreport", description="Open the bug report form", aliases=['report'])
    async def bugreport(self, ctx):
        await ctx.message.delete()
        view = self.BugReportButton()
        bug = await ctx.send("Click the button below to report a bug!", view=view)
        await asyncio.sleep(15)
        await bug.delete()

    @commands.command(name="viewbugs", description="View all bug reports", aliases=['bugs'])
    @commands.is_owner()
    async def viewbugs(self, ctx):
        await ctx.message.delete()
        with open(self.bug_reports_file, "r") as f:
            reports = json.load(f)

        if not reports:
            await ctx.send("No bug reports found!")
            return

        view = self.BugReportPaginator(reports)
        report = reports[0]
        embed = discord.Embed(
            title=f"Bug Report #{report['report_id']}",
            description=f"**Title:** {report['title']}\n\n"
                       f"**Description:** {report['description']}\n\n"
                       f"**Steps to Reproduce:** {report['steps']}\n\n"
                       f"**Reported by:** {report['author_name']}\n"
                       f"**Status:** {report['status']}\n"
                       f"**Date:** {report['timestamp']}",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Page 1/{len(reports)}")
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(BugReport(bot))
