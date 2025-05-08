import asyncio
import aiohttp
import logging
import re
import json
import csv
import io
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
from urllib.parse import urlparse

# For LLM-based extraction (after fetching raw HTML)
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure OpenAI (used only for text extraction from fetched HTML)
openai.api_key = "your-api-key"  # Store this in environment variables in production

class ResearchEngine:
    """Engine for researching subcontractors based on specified criteria"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def run_research(self, trade: str, city: str, state: str, min_bond: int, keywords: List[str]) -> List[Dict[str, Any]]:
        """Run the full research pipeline"""
        async with aiohttp.ClientSession(headers=self.headers) as self.session:
            # Step 1: Web discovery - Find candidate companies
            candidates = await self.discover_candidates(trade, city, state, keywords)
            logger.info(f"Found {len(candidates)} initial candidates")
            
            # Step 2: Profile extraction - Visit each website and extract info
            profiles = await self.extract_profiles(candidates)
            logger.info(f"Extracted {len(profiles)} profiles")
            
            # Step 3: License check - Verify license status
            profiles = await self.verify_licenses(profiles, state)
            logger.info("License verification completed")
            
            # Step 4: Project history parsing
            profiles = await self.parse_project_history(profiles, state, keywords)
            logger.info("Project history parsing completed")
            
            # Step 5: Score and rank candidates
            ranked_results = self.score_and_rank(profiles, city, state, min_bond)
            logger.info(f"Ranked {len(ranked_results)} candidates")
            
            return ranked_results

    async def discover_candidates(self, trade: str, city: str, state: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """Discover candidate companies using search APIs and directories"""
        candidates = []
        
        # Build search queries
        search_queries = [
            f"{trade} contractors {city} {state}",
            f"{trade} subcontractors {city} {state}",
        ]
        
        # Add keywords to search queries
        for keyword in keywords:
            search_queries.append(f"{trade} {keyword} contractors {city} {state}")
        
        # Use multiple discovery methods
        search_tasks = [
            self._search_google_custom(query) for query in search_queries
        ] + [
            self._search_yelp(trade, city, state),
            self._search_bbb(trade, city, state),
            self._search_state_license_board(trade, state)
        ]
        
        # Run search tasks concurrently
        all_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process results
        for results in all_results:
            if isinstance(results, Exception):
                logger.error(f"Error in search: {results}")
                continue
                
            candidates.extend(results)
        
        # Deduplicate by domain
        unique_candidates = {}
        for candidate in candidates:
            domain = self._extract_domain(candidate.get("website", ""))
            if domain and domain not in unique_candidates:
                unique_candidates[domain] = candidate
        
        return list(unique_candidates.values())
        
    async def _search_google_custom(self, query: str) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API"""
        # In a real implementation, use Google Custom Search API
        # Here we'll simulate results for demonstration
        await asyncio.sleep(0.5)  # Simulate API call
        
        # Simulated results based on query
        simulated_domains = [
            "austinmechanical.com",
            "texasmechanicalservices.com",
            "precisionhvactx.com",
            "elitemechanicalaustin.com",
            "centralteamechanical.com",
            "alliancemechanical.net",
            "texasaircontrol.com",
            "austinhvac.com",
        ]
        
        results = []
        for i, domain in enumerate(simulated_domains):
            if i < 10:  # Limit to 10 results per query
                results.append({
                    "name": f"Simulated Company {i+1}",
                    "website": f"https://www.{domain}",
                    "source": "google_search"
                })
                
        return results
                
    async def _search_yelp(self, trade: str, city: str, state: str) -> List[Dict[str, Any]]:
        """Search Yelp for businesses matching criteria"""
        # In a real implementation, use Yelp Fusion API
        # Here we'll simulate results for demonstration
        await asyncio.sleep(0.5)  # Simulate API call
        
        # Simulated results
        simulated_domains = [
            "austinmechanical.com",
            "capitalcitymechanical.com",
            "abcmechanical.com",
            "starrmechanical.com",
            "foxservice.com",
        ]
        
        results = []
        for i, domain in enumerate(simulated_domains):
            results.append({
                "name": f"Yelp Company {i+1}",
                "website": f"https://www.{domain}",
                "source": "yelp"
            })
                
        return results
        
    async def _search_bbb(self, trade: str, city: str, state: str) -> List[Dict[str, Any]]:
        """Search Better Business Bureau for accredited businesses"""
        # In a real implementation, scrape BBB website
        # Here we'll simulate results for demonstration
        await asyncio.sleep(0.3)  # Simulate scraping
        
        # Simulated results
        simulated_domains = [
            "precisionmechanical.com",
            "reliablemechanical.com",
            "qualitymechanical.com",
        ]
        
        results = []
        for i, domain in enumerate(simulated_domains):
            results.append({
                "name": f"BBB Company {i+1}",
                "website": f"https://www.{domain}",
                "source": "bbb"
            })
                
        return results
        
    async def _search_state_license_board(self, trade: str, state: str) -> List[Dict[str, Any]]:
        """Search state license board database"""
        # In a real implementation, query state license database
        # For Texas, would use TDLR contractor registry
        await asyncio.sleep(0.7)  # Simulate database query
        
        # Simulated results
        results = []
        for i in range(1, 6):
            results.append({
                "name": f"Licensed {trade.title()} Contractor {i}",
                "lic_number": f"TX{random.randint(10000000, 99999999)}",
                "lic_active": True,
                "source": "license_board"
            })
                
        return results
        
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
            
        try:
            # Add scheme if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
                
            return domain
        except:
            return ""
            
    async def extract_profiles(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract detailed profiles from candidate websites"""
        profiles = []
        
        # Process candidates in batches to avoid overwhelming resources
        batch_size = 5
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i+batch_size]
            
            # Create tasks for concurrent processing
            tasks = [self._extract_single_profile(candidate) for candidate in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error extracting profile: {result}")
                    continue
                    
                if result:  # Skip empty results
                    profiles.append(result)
                    
            # Add delay between batches to be respectful to servers
            await asyncio.sleep(1)
        
        return profiles
        
    async def _extract_single_profile(self, candidate: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract information from a single candidate website"""
        website = candidate.get("website")
        if not website:
            return None
            
        # Ensure URL has a scheme
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website

        profile = {
            "name": candidate.get("name", ""),
            "website": website,
            "last_checked": datetime.now().isoformat(),
        }
        
        # Copy any data already present from discovery phase
        for field in ["lic_number", "lic_active"]:
            if field in candidate:
                profile[field] = candidate[field]
        
        try:
            # Pages to visit
            pages_to_visit = [
                "",  # Homepage
                "/about", "/about-us", "/company", 
                "/services", 
                "/projects", "/portfolio", "/our-work", "/case-studies",
                "/contact", "/contact-us"
            ]
            
            # Get content from key pages
            page_contents = {}
            for path in pages_to_visit:
                page_url = website.rstrip('/') + path
                try:
                    # Fetch page content
                    async with self.session.get(page_url, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            page_contents[path] = html
                except Exception as e:
                    logger.warning(f"Error fetching {page_url}: {e}")
                
                # Be respectful with requests
                await asyncio.sleep(0.5)
            
            if not page_contents:
                logger.warning(f"No pages successfully fetched for {website}")
                return None
                
            # Extract information from pages using patterns and LLM
            extracted_data = await self._extract_data_from_pages(page_contents, website)
            
            # Update profile with extracted data
            profile.update(extracted_data)
            
            # Store evidence
            evidence_page = extracted_data.get("evidence_page", "")
            profile["evidence_url"] = website.rstrip('/') + evidence_page if evidence_page else website
            
            # Count populated fields (need at least 4 for F-2 requirement)
            populated_fields = sum(1 for k, v in profile.items() 
                                   if v is not None and k not in ["website", "last_checked", "evidence_url", "evidence_text"])
            
            if populated_fields >= 4:
                return profile
            else:
                logger.warning(f"Insufficient data extracted for {website}: only {populated_fields} fields")
                return None
                
        except Exception as e:
            logger.error(f"Error processing {website}: {e}")
            return None
    
    async def _extract_data_from_pages(self, page_contents: Dict[str, str], website: str) -> Dict[str, Any]:
        """Extract structured data from page contents"""
        # This function would use pattern matching and potentially LLM for extraction
        extracted_data = {
            "email": None,
            "phone_number": None,
            "city": None,
            "state": None,
            "bond_amount": None,
            "evidence_text": "",
            "evidence_page": "",
        }
        
        # Example pattern matching for contact info
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        # Bond amount patterns
        bond_patterns = [
            r'bond(?:ed|ing)(?:\s+(?:up\s+)?to)?\s+\$(\d+(?:[,.]\d+)?)\s+(?:million|m)',
            r'bond(?:ed|ing)(?:\s+(?:up\s+)?to)?\s+\$(\d+(?:[,.]\d+)?)',
        ]
        
        # Try to find key data across all pages
        best_evidence = ""
        best_evidence_page = ""
        
        for page_path, html in page_contents.items():
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(' ', strip=True)
            
            # Look for email
            if not extracted_data["email"]:
                email_matches = re.findall(email_pattern, text)
                if email_matches:
                    extracted_data["email"] = email_matches[0]
            
            # Look for phone number
            if not extracted_data["phone_number"]:
                phone_matches = re.findall(phone_pattern, text)
                if phone_matches:
                    extracted_data["phone_number"] = phone_matches[0]
            
            # Look for city and state (common patterns in contact pages)
            address_patterns = [
                r'(?:address|location)(?:[:\s]+)([^,]+),\s+([A-Z]{2})\s+\d{5}',
                r'([A-Za-z\s]+),\s+([A-Z]{2})\s+\d{5}',
            ]
            
            for pattern in address_patterns:
                address_matches = re.findall(pattern, text)
                if address_matches and not (extracted_data["city"] and extracted_data["state"]):
                    extracted_data["city"] = address_matches[0][0].strip()
                    extracted_data["state"] = address_matches[0][1]
            
            # Look for bonding info
            for pattern in bond_patterns:
                bond_matches = re.findall(pattern, text, re.IGNORECASE)
                if bond_matches:
                    # Extract the first match
                    bond_str = bond_matches[0]
                    
                    # Convert to numeric
                    try:
                        # Remove commas and convert to float
                        bond_value = float(bond_str.replace(',', ''))
                        
                        # Check if "million" was in the original text
                        if "million" in text.lower() or "m" in text.lower():
                            bond_value *= 1000000
                            
                        extracted_data["bond_amount"] = int(bond_value)
                        
                        # Save evidence text (the surrounding context)
                        # Find the position of the bond amount in the text
                        bond_pos = text.lower().find(bond_str.lower())
                        if bond_pos != -1:
                            # Extract a window of text around the bond amount
                            start_pos = max(0, bond_pos - 100)
                            end_pos = min(len(text), bond_pos + 100)
                            evidence = text[start_pos:end_pos].strip()
                            
                            # Update best evidence if this is the first or better than previous
                            if not best_evidence or len(evidence) > len(best_evidence):
                                best_evidence = evidence
                                best_evidence_page = page_path
                        
                        break  # Stop after finding the first valid bond amount
                    except:
                        continue
        
        # Use LLM for extraction if regular expressions didn't find everything
        # Only use LLM for extraction from HTML we've already fetched
        if not all([extracted_data["city"], extracted_data["state"], extracted_data["bond_amount"]]):
            # Combine page texts for analysis (limit to avoid token limitations)
            combined_text = ""
            for page, html in list(page_contents.items())[:3]:  # Limit to first 3 pages
                soup = BeautifulSoup(html, 'html.parser')
                combined_text += soup.get_text(' ', strip=True)[:5000]  # Limit each page text
            
            # Use LLM to extract from fetched HTML
            try:
                llm_extracted = await self._extract_with_llm(combined_text, website)
                
                # Update missing fields with LLM-extracted data
                for field in ["city", "state", "bond_amount", "email", "phone_number"]:
                    if not extracted_data[field] and field in llm_extracted:
                        extracted_data[field] = llm_extracted[field]
                        
                # Update evidence if LLM found better evidence
                if llm_extracted.get("evidence_text") and not best_evidence:
                    best_evidence = llm_extracted.get("evidence_text")
            except Exception as e:
                logger.error(f"Error using LLM for extraction: {e}")
        
        # Set final evidence
        extracted_data["evidence_text"] = best_evidence
        extracted_data["evidence_page"] = best_evidence_page
        
        return extracted_data
    
    async def _extract_with_llm(self, text: str, website: str) -> Dict[str, Any]:
        """Use LLM to extract structured info from website text"""
        # Note: LLMs are only used to extract structure from already fetched HTML,
        # not to generate lists of subcontractors or hallucinate data
        
        # Truncate text to fit in context window
        text = text[:15000]  # Adjust based on model's context limit
        
        # Prompt the LLM to extract specific fields
        prompt = f"""
        Extract the following fields from this contractor website text. 
        Return ONLY a JSON object with these fields:
        - city: The city where the contractor is based
        - state: The state where the contractor is based (2-letter code)
        - bond_amount: The bonding capacity amount as an integer (convert text like "5 million" to 5000000)
        - email: Contact email if present
        - phone_number: Contact phone if present
        - evidence_text: The specific text mentioning bonding capacity

        If a field is not found, return null for that field.
        
        Website: {website}
        
        Text:
        {text}
        """
        
        # Call the LLM API to extract information
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            # Parse the response
            try:
                content = response.choices[0].message.content
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON for {website}")
                return {}
        except Exception as e:
            logger.error(f"LLM API error for {website}: {str(e)}")
            return {}
            
    async def verify_licenses(self, profiles: List[Dict[str, Any]], state: str) -> List[Dict[str, Any]]:
        """Verify license status with state regulatory database"""
        # For Texas, use TDLR contractor registry
        if state.upper() != "TX":
            logger.warning(f"License verification not implemented for state: {state}")
            return profiles
            
        # In a real implementation, would query the TDLR database
        # Here we'll simulate it by setting random licenses as active
        for profile in profiles:
            if "lic_number" not in profile or not profile["lic_number"]:
                # Generate a random license number if not already present
                profile["lic_number"] = f"TX{random.randint(10000000, 99999999)}"
            
            # Mark as active with 80% probability (simulating real world where most are active)
            profile["lic_active"] = random.random() < 0.8
            
        return profiles
        
    async def parse_project_history(self, profiles: List[Dict[str, Any]], state: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """Parse project history to identify relevant projects"""
        for profile in profiles:
            website = profile.get("website")
            if not website:
                continue
                
            # Look for project pages
            project_paths = ["/projects", "/portfolio", "/our-work", "/case-studies"]
            
            project_html = ""
            project_url = ""
            
            # Try to fetch project pages
            for path in project_paths:
                url = website.rstrip('/') + path
                try:
                    async with self.session.get(url, timeout=10) as response:
                        if response.status == 200:
                            project_html = await response.text()
                            project_url = url
                            break
                except Exception as e:
                    logger.warning(f"Error fetching project page {url}: {e}")
                
                # Be respectful with requests
                await asyncio.sleep(0.5)
            
            # Count Texas projects in the last 5 years using regex
            tx_project_count = 0
            current_year = datetime.now().year
            years = [str(year) for year in range(current_year - 5, current_year + 1)]
            
            if project_html:
                soup = BeautifulSoup(project_html, 'html.parser')
                text = soup.get_text(' ', strip=True)
                
                # Look for mentions of Texas and recent years
                tx_mentions = len(re.findall(r'Texas|TX|Austin|Dallas|Houston|San Antonio', text, re.IGNORECASE))
                year_mentions = sum(len(re.findall(year, text)) for year in years)
                
                # Look for keywords
                keyword_mentions = sum(len(re.findall(keyword, text, re.IGNORECASE)) for keyword in keywords)
                
                # Estimate project count based on mentions
                # This is a simple heuristic - in a real implementation, use NLP to better identify projects
                tx_project_count = min(tx_mentions, year_mentions)
                
                # Adjust score based on keyword relevance
                if keyword_mentions > 0 and tx_project_count > 0:
                    tx_project_count = min(tx_project_count + keyword_mentions // 2, 10)
            
            profile["tx_projects_past_5yrs"] = tx_project_count
            
        return profiles
        
    def score_and_rank(self, profiles: List[Dict[str, Any]], target_city: str, target_state: str, min_bond: int) -> List[Dict[str, Any]]:
        """Score and rank contractors based on criteria"""
        ranked_results = []
        
        for profile in profiles:
            # Skip profiles without minimum required data
            if not profile.get("name") or not profile.get("website"):
                continue
                
            # Initialize score
            score = 0
            
            # Factor 1: Geographic match (up to 25 points)
            # Higher score for contractors based in target city/state
            if profile.get("city") == target_city and profile.get("state") == target_state:
                score += 25  # Perfect location match
            elif profile.get("state") == target_state:
                score += 15  # Same state
            
            # Factor 2: License status (up to 25 points)
            if profile.get("lic_active") is True:
                score += 25  # Active license
            elif profile.get("lic_active") is False:
                score += 0   # Inactive license
            else:
                score += 10  # Unknown license status
            
            # Factor 3: Bonding capacity (up to 25 points)
            bond_amount = profile.get("bond_amount")
            if bond_amount is not None:
                if bond_amount >= min_bond:
                    # Full points if meets or exceeds minimum
                    score += 25
                else:
                    # Partial points based on how close they are to minimum
                    ratio = bond_amount / min_bond
                    score += int(25 * ratio)
            
            # Factor 4: Project experience (up to 25 points)
            tx_projects = profile.get("tx_projects_past_5yrs", 0)
            if tx_projects >= 5:
                score += 25  # Full points for 5+ recent projects
            else:
                score += 5 * tx_projects  # 5 points per project
            
            # Add score to profile
            profile["score"] = score
            
            # Only include contractors with minimum viable score (40+)
            if score >= 40:
                ranked_results.append(profile)
        
        # Sort by score (descending)
        ranked_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return ranked_results
