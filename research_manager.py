from agents import Runner, trace, gen_trace_id
from downloader_agent import download_agent
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio

class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, generating report..."
            report = await self.write_report(query, search_results)
            yield report.markdown_report
            pdf_result = await Runner.run(
                download_agent,
                f"Filename: report.pdf\n\n{report.markdown_report}",
            )

            url = None
            out = getattr(pdf_result, "final_output", None)

            if isinstance(out, dict):
                url = out.get("url") or out.get("path")
            elif isinstance(out, str):
                # try JSON first
                import json, re
                try:
                    data = json.loads(out)
                    url = data.get("url") or data.get("path")
                except Exception:
                    m = re.search(r'(?:https?://\S+\.pdf|/static/\S+\.pdf)', out)
                    url = m.group(0) if m else out.strip()

            if not url:
                url = "/static/exports/report.pdf"  # safe default

            yield f"PDF ready: {url}"
            await self.send_email(report)
            yield "Email sent, research complete"
            # yield report.markdown_report
        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def download_report(self, report: ReportData):
        print("Generating a downloadable report...")
        result = await Runner.run(
            download_agent,
            report.markdown_report,
        )
        return result.final_output

    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
        return report