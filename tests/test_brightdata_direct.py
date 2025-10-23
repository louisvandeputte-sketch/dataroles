#!/usr/bin/env python3
"""Direct test of Bright Data API to diagnose hanging issue."""

import asyncio
import httpx
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

async def test_brightdata_api():
    """Test Bright Data API directly with detailed logging."""
    
    api_token = os.getenv('BRIGHTDATA_API_TOKEN')
    dataset_id = os.getenv('BRIGHTDATA_DATASET_ID')
    
    logger.info(f"Testing Bright Data API")
    logger.info(f"Dataset ID: {dataset_id}")
    logger.info(f"API Token: {'SET' if api_token else 'NOT SET'} ({len(api_token) if api_token else 0} chars)")
    
    # Create client with aggressive timeouts
    client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        },
        timeout=httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=10.0,
            pool=10.0
        )
    )
    
    # Minimal payload
    payload = {
        "input": [{
            "keyword": "Data Engineer",
            "location": "Belgium",
            "time_range": "Past 24 hours",
            "country": "BE"
        }]
    }
    
    url = "https://api.brightdata.com/datasets/v3/trigger"
    params = {
        "dataset_id": dataset_id,
        "include_errors": "true",
        "type": "discover_new",
        "discover_by": "keyword"
    }
    
    try:
        logger.info(f"Sending POST request to {url}")
        logger.info(f"Params: {params}")
        logger.info(f"Payload: {payload}")
        
        logger.info("Waiting for response...")
        response = await client.post(url, json=payload, params=params)
        
        logger.success(f"✅ Got response! Status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response body: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            logger.success(f"✅ Success! Snapshot ID: {data.get('snapshot_id')}")
            return True
        else:
            logger.error(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except httpx.TimeoutException as e:
        logger.error(f"❌ TIMEOUT: {e}")
        logger.error("The API call timed out - this is likely the hanging issue!")
        return False
    except httpx.ConnectError as e:
        logger.error(f"❌ CONNECTION ERROR: {e}")
        return False
    except Exception as e:
        logger.exception(f"❌ UNEXPECTED ERROR: {e}")
        return False
    finally:
        await client.aclose()

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("BRIGHT DATA API DIRECT TEST")
    logger.info("="*60)
    
    result = asyncio.run(test_brightdata_api())
    
    if result:
        logger.success("\n✅ Test PASSED - API is working")
    else:
        logger.error("\n❌ Test FAILED - API has issues")
