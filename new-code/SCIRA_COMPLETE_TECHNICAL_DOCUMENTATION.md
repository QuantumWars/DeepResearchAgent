# Scira AI Search Platform - Complete Technical Documentation

> **Generated on**: ${new Date().toISOString().split('T')[0]}
> **Version**: Based on codebase analysis
> **Scope**: Complete system architecture and implementation details

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Search API Flow](#search-api-flow)
3. [Core Search Systems](#core-search-systems)
4. [Extreme Search Deep Research](#extreme-search-deep-research)
5. [Multi-Provider Search Strategy](#multi-provider-search-strategy)
6. [Content Processing Pipeline](#content-processing-pipeline)
7. [Supermemory Integration](#supermemory-integration)
8. [Real-Time Streaming Architecture](#real-time-streaming-architecture)
9. [Authentication & Rate Limiting](#authentication--rate-limiting)
10. [Database Schema & Performance](#database-schema--performance)
11. [File Structure & Key Components](#file-structure--key-components)
12. [Error Handling & Fallbacks](#error-handling--fallbacks)
13. [Security & Privacy](#security--privacy)
14. [Environment Configuration](#environment-configuration)
15. [Deployment & Operations](#deployment--operations)

---

## Architecture Overview

### **System Design**
Scira is a Next.js-based AI chat application with advanced search capabilities built on a modern tech stack:

- **Framework**: Next.js 16 (React 19)
- **Database**: PostgreSQL with Drizzle ORM
- **Caching**: Redis (Upstash)
- **Authentication**: Better Auth
- **AI Providers**: Multiple providers (OpenAI, Anthropic, XAI, Groq, Google, Cohere)
- **Search APIs**: Exa, Tavily, Firecrawl, Parallel AI
- **Payment**: Polar (for subscription management)
- **Deployment**: Vercel

### **Core Components**
1. **Search API Router**: `app/api/search/route.ts`
2. **Search Tools**: `lib/tools/` directory
3. **Database Layer**: `lib/db/` with 27 optimized indexes
4. **Authentication**: Better Auth integration
5. **Streaming System**: Real-time SSE-based communication

### **System Flow Diagram**
```
User Query → API Route → Authentication → Rate Limiting → AI Model → Tool Selection → Multi-Provider Search → Content Processing → Streaming Response → Database Storage
```

---

## Search API Flow

### **Entry Point**: `app/api/search/route.ts:107-670`

#### **Request Structure**
```typescript
const {
  messages,
  model,                    // AI model selection
  group,                    // 'extreme' for deep research
  timezone,
  id,                       // Chat ID
  selectedVisibilityType,
  isCustomInstructionsEnabled,
  searchProvider,           // 'exa' | 'parallel' | 'tavily' | 'firecrawl'
  selectedConnectors,       // Google Drive, Notion, OneDrive
} = await req.json();
```

#### **Phase 1: Authentication & Validation** (Lines 125-155)
```typescript
// CRITICAL PATH: Get auth status first
const lightweightUser = await getLightweightUser();

// Rate limit check for unauthenticated users
if (!lightweightUser) {
  const identifier = getClientIdentifier(req);
  const { success, limit, reset } = await unauthenticatedRateLimit.limit(identifier);
  if (!success) {
    return new ChatSDKError('rate_limit:api', `Rate limit exceeded`).toResponse();
  }
}

// Model-specific authentication checks
if (requiresAuthentication(model)) {
  return new ChatSDKError('unauthorized:model', `${model} requires authentication`).toResponse();
}

// Extreme search requires authentication
if (group === 'extreme' && !lightweightUser) {
  return new ChatSDKError('unauthorized:auth', 'Authentication required for Extreme Search').toResponse();
}
```

#### **Phase 2: Parallel Operations** (Lines 157-282)
```typescript
// START ALL CRITICAL PARALLEL OPERATIONS IMMEDIATELY
const configPromise = getGroupConfig(group);
const fullUserPromise = lightweightUser ? getCurrentUser() : Promise.resolve(null);
const customInstructionsPromise = lightweightUser && (isCustomInstructionsEnabled ?? true)
  ? fullUserPromise.then(user => user ? getCachedCustomInstructionsByUserId(user.id) : null)
  : Promise.resolve(null);
```

#### **Phase 3: Critical Checks for Authenticated Users**
```typescript
let criticalChecksPromise: Promise<{
  canProceed: boolean;
  error?: any;
  isProUser: boolean;
  messageCount?: number;
  extremeSearchUsage?: number;
}>;

if (lightweightUser && !isProUser) {
  criticalChecksPromise = Promise.all([
    fullUserPromise,
    chatValidationPromise,
  ]).then(async ([user]) => {
    const [messageCountResult, extremeSearchUsage] = await Promise.all([
      getUserMessageCount(user),
      getExtremeSearchUsageCount(user),
    ]);

    if (messageCountResult.count >= 100) {
      throw new ChatSDKError('rate_limit:chat', 'Daily search limit reached');
    }

    return { canProceed: true, isProUser: false, messageCount: messageCountResult.count };
  });
}
```

#### **Phase 4: Streaming Response** (Lines 287-661)
```typescript
const stream = createUIMessageStream<ChatMessage>({
  execute: async ({ writer: dataStream }) => {
    const [criticalResult, { tools: activeTools, instructions }, customInstructionsResult, user] =
      await Promise.all([criticalChecksPromise, configPromise, customInstructionsPromise, fullUserPromise]);

    if (!criticalResult.canProceed) {
      throw criticalResult.error;
    }

    // Save user message BEFORE streaming
    if (user) {
      await saveMessages({
        messages: [{
          chatId: id,
          id: messages[messages.length - 1].id,
          role: 'user',
          parts: messages[messages.length - 1].parts,
          createdAt: new Date(),
        }],
      });
    }

    const result = streamText({
      model: scira.languageModel(model),
      messages: convertToModelMessages(messages),
      ...getModelParameters(model),
      stopWhen: stepCountIs(5),
      maxRetries: 10,
      activeTools: [...activeTools],
      experimental_transform: markdownJoinerTransform(),
      system: instructions +
        (customInstructions && (isCustomInstructionsEnabled ?? true)
          ? `\n\nThe user's custom instructions are: ${customInstructions?.content}`
          : '\n'),
      toolChoice: 'auto',
      tools: (() => {
        const baseTools = {
          web_search: webSearchTool(dataStream, searchProvider),
          extreme_search: extremeSearchTool(dataStream),
          x_search: xSearchTool,
          // ... other tools
        };

        if (!user) return baseTools;

        const memoryTools = createMemoryTools(user.id);
        return {
          ...baseTools,
          search_memories: memoryTools.searchMemories,
          add_memory: memoryTools.addMemory,
          connectors_search: createConnectorsSearchTool(user.id, selectedConnectors),
        };
      })(),
    });

    result.consumeStream();
    dataStream.merge(result.toUIMessageStream({ sendReasoning: true }));
  },
});

return new Response(stream.pipeThrough(new JsonToSseTransformStream()));
```

---

## Core Search Systems

### **1. Web Search Tool**: `lib/tools/web-search.ts:629-718`

#### **Strategy Pattern Implementation**
```typescript
interface SearchStrategy {
  search(
    queries: string[],
    options: {
      maxResults: number[];
      topics: ('general' | 'news')[];
      quality: ('default' | 'best')[];
      dataStream?: UIMessageStreamWriter<ChatMessage>;
    },
  ): Promise<{ searches: Array<{ query: string; results: any[]; images: any[] }> }>;
}
```

#### **Search Strategies**

##### **Parallel AI Strategy** (`Lines 105-243`)
```typescript
class ParallelSearchStrategy implements SearchStrategy {
  constructor(private parallel: Parallel, private firecrawl: FirecrawlApp) {}

  async search(queries, options) {
    const limitedQueries = queries.slice(0, 5);

    // Send start notifications
    limitedQueries.forEach((query, index) => {
      options.dataStream?.write({
        type: 'data-query_completion',
        data: { query, index, total: limitedQueries.length, status: 'started' },
      });
    });

    const perQueryPromises = limitedQueries.map(async (query, index) => {
      const [singleResponse, firecrawlImages] = await Promise.all([
        this.parallel.beta.search({
          objective: query,
          search_queries: [query],
          processor: currentQuality === 'best' ? 'pro' : 'base',
          max_results: Math.max(currentMaxResults, 10),
          max_chars_per_result: 1000,
        }),
        this.firecrawl.search(query, { sources: ['images'], limit: 3 }),
      ]);

      const results = (singleResponse?.results || []).map((result: any) => ({
        url: result.url,
        title: cleanTitle(result.title || ''),
        content: Array.isArray(result.excerpts)
          ? result.excerpts.join(' ').substring(0, 1000)
          : (result.content || '').substring(0, 1000),
      }));

      return { query, results, images: firecrawlImages.images || [] };
    });

    return { searches: await Promise.all(perQueryPromises) };
  }
}
```

##### **Tavily Strategy** (`Lines 246-361`)
```typescript
class TavilySearchStrategy implements SearchStrategy {
  async search(queries, options) {
    const searchPromises = queries.map(async (query, index) => {
      const currentTopic = options.topics[index] || 'general';
      const currentMaxResults = options.maxResults[index] || 10;

      const tavilyData = await this.tvly.search(query, {
        topic: currentTopic,
        days: currentTopic === 'news' ? 7 : undefined,
        maxResults: currentMaxResults,
        searchDepth: options.quality[index] === 'best' ? 'advanced' : 'basic',
        includeAnswer: true,
        includeImages: true,
        includeImageDescriptions: true,
      });

      const results = deduplicateByDomainAndUrl(tavilyData.results).map((obj: any) => ({
        url: obj.url,
        title: cleanTitle(obj.title || ''),
        content: obj.content,
        published_date: currentTopic === 'news' ? obj.published_date : undefined,
      }));

      // Process images with validation
      const images = await Promise.all(
        deduplicateByDomainAndUrl(tavilyData.images || []).map(async ({ url, description }) => {
          const sanitizedUrl = sanitizeUrl(url);
          const imageValidation = await isValidImageUrl(sanitizedUrl);
          return imageValidation.valid ? {
            url: imageValidation.redirectedUrl || sanitizedUrl,
            description: description || '',
          } : null;
        }),
      ).then(results => results.filter(img => img !== null));

      return { query, results, images };
    });

    return { searches: await Promise.all(searchPromises) };
  }
}
```

##### **Firecrawl Strategy** (`Lines 364-493`)
```typescript
class FirecrawlSearchStrategy implements SearchStrategy {
  async search(queries, options) {
    const searchPromises = queries.map(async (query, index) => {
      const sources = [] as ('web' | 'news' | 'images')[];

      if (options.topics[index] === 'news') {
        sources.push('news', 'web');
      } else {
        sources.push('web');
      }
      sources.push('images');

      const firecrawlData = await this.firecrawl.search(query, {
        sources,
        limit: options.maxResults[index] || 10,
      });

      let results: any[] = [];

      // Process web results
      if (firecrawlData?.web && Array.isArray(firecrawlData.web)) {
        const webResults = firecrawlData.web.filter(isSearchResultWeb);
        results = deduplicateByDomainAndUrl(webResults).map((result) => ({
          url: result.url,
          title: cleanTitle(result.title || ''),
          content: result.description || '',
        }));
      }

      // Process news results
      if (firecrawlData?.news && Array.isArray(firecrawlData.news)) {
        const newsResults = firecrawlData.news.filter(isSearchResultNewsWithUrl);
        const processedNews = deduplicateByDomainAndUrl(newsResults).map((result) => ({
          url: result.url,
          title: cleanTitle(result.title || ''),
          content: result.snippet || '',
          published_date: result.date || undefined,
        }));
        results = [...processedNews, ...results];
      }

      return { query, results, images: firecrawlData.images || [] };
    });

    return { searches: await Promise.all(searchPromises) };
  }
}
```

##### **Exa Strategy** (`Lines 496-607`)
```typescript
class ExaSearchStrategy implements SearchStrategy {
  async search(queries, options) {
    const searchPromises = queries.map(async (query, index) => {
      const currentTopic = options.topics[index] || 'general';
      const currentQuality = options.quality[index] || 'default';

      const searchOptions: any = {
        text: true,
        type: currentQuality === 'best' ? 'hybrid' : 'auto',
        numResults: Math.max(options.maxResults[index] || 10, 10),
        livecrawl: 'preferred',
        useAutoprompt: true,
        category: currentTopic === 'news' ? 'news' : '',
      };

      const data = await this.exa.searchAndContents(query, searchOptions);

      const collectedImages: { url: string; description: string }[] = [];
      const results = data.results.map((result) => {
        if (result.image) {
          collectedImages.push({
            url: result.image,
            description: cleanTitle(result.title || result.text?.substring(0, 100) + '...' || ''),
          });
        }

        return {
          url: result.url,
          title: cleanTitle(result.title || ''),
          content: (result.text || '').substring(0, 1000),
          published_date: result.publishedDate || undefined,
          author: result.author || undefined,
        };
      });

      return {
        query,
        results: deduplicateByDomainAndUrl(results),
        images: deduplicateByDomainAndUrl(collectedImages),
      };
    });

    return { searches: await Promise.all(searchPromises) };
  }
}
```

#### **Provider Factory** (`Lines 610-627`)
```typescript
const createSearchStrategy = (
  provider: 'exa' | 'parallel' | 'tavily' | 'firecrawl',
  clients: {
    exa: Exa;
    parallel: Parallel;
    firecrawl: FirecrawlApp;
    tvly: TavilyClient;
  },
): SearchStrategy => {
  const strategies = {
    parallel: () => new ParallelSearchStrategy(clients.parallel, clients.firecrawl),
    tavily: () => new TavilySearchStrategy(clients.tvly),
    firecrawl: () => new FirecrawlSearchStrategy(clients.firecrawl),
    exa: () => new ExaSearchStrategy(clients.exa),
  };

  return strategies[provider]();
};
```

#### **Content Processing Functions**

##### **Title Cleaning** (`Lines 17-24`)
```typescript
const cleanTitle = (title: string): string => {
  return title
    .replace(/\[.*?\]/g, '') // Remove [content]
    .replace(/\(.*?\)/g, '') // Remove (content)
    .replace(/\s+/g, ' ') // Replace multiple spaces with single space
    .trim(); // Remove leading/trailing whitespace
};
```

##### **Domain and URL Deduplication** (`Lines 26-42`)
```typescript
const deduplicateByDomainAndUrl = <T extends { url: string }>(items: T[]): T[] => {
  const seenDomains = new Set<string>();
  const seenUrls = new Set<string>();

  return items.filter((item) => {
    const domain = extractDomain(item.url);
    const isNewUrl = !seenUrls.has(item.url);
    const isNewDomain = !seenDomains.has(domain);

    if (isNewUrl && isNewDomain) {
      seenUrls.add(item.url);
      seenDomains.add(domain);
      return true;
    }
    return false;
  });
};
```

##### **Domain Extraction** (`Lines 11-15`)
```typescript
const extractDomain = (url: string | null | undefined): string => {
  if (!url || typeof url !== 'string') return '';
  const urlPattern = /^https?:\/\/([^/?#]+)(?:[/?#]|$)/i;
  return url.match(urlPattern)?.[1] || url;
};
```

##### **Image URL Validation** (`Lines 82-89`)
```typescript
const isValidImageUrl = async (url: string): Promise<{ valid: boolean; redirectedUrl?: string }> => {
  try {
    const urlObj = new URL(url);
    return { valid: true, redirectedUrl: urlObj.href };
  } catch {
    return { valid: false };
  }
};
```

---

## Extreme Search Deep Research

### **Main Function**: `lib/tools/extreme-search.ts:192-731`

#### **Research Planning Phase** (`Lines 208-245`)
```typescript
const extremeSearch = async (prompt: string, dataStream: UIMessageStreamWriter<ChatMessage> | undefined): Promise<Research> => {
  const allSources: SearchResult[] = [];

  // Planning notification
  if (dataStream) {
    dataStream.write({
      type: 'data-extreme_search',
      data: {
        kind: 'plan',
        status: { title: 'Planning research' },
      },
    });
  }

  // AI research planning
  const { object: result } = await generateObject({
    model: scira.languageModel('scira-grok-4-fast-think'),
    schema: z.object({
      plan: z.array(z.object({
        title: z.string().min(10).max(70).describe('A title for the research topic'),
        todos: z.array(z.string()).min(3).max(5).describe('A list of what to research for the given title'),
      })).min(1).max(5),
    }),
    prompt: `
Plan out the research for the following topic: ${prompt}.

Today's Date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: '2-digit', weekday: 'short' })}

Plan Guidelines:
- Break down the topic into key aspects to research
- Generate specific, diverse search queries for each aspect
- The plan is limited to 15 actions, do not exceed this limit!
- Keep the titles concise and to the point, no more than 70 characters
- Mention if the topic needs to use the xSearch tool
- Mention any need for visualizations in the plan
- Make the plan technical and specific to the topic`,
  });

  const plan = result.plan;
  const totalTodos = plan.reduce((acc, curr) => acc + curr.todos.length, 0);

  // Plan completion notification
  if (dataStream) {
    dataStream.write({
      type: 'data-extreme_search',
      data: {
        kind: 'plan',
        status: { title: 'Research plan ready, starting up research agent' },
        plan,
      },
    });
  }

  // ... continue with research agent execution
};
```

#### **Autonomous Research Agent** (`Lines 265-695`)
```typescript
const { text } = await generateText({
  model: scira.languageModel('scira-grok-4-fast-think'),
  stopWhen: stepCountIs(totalTodos),
  system: `
You are an autonomous deep research analyst. Your goal is to research the given research plan thoroughly with the given tools.

Today's Date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: '2-digit', weekday: 'short' })}.

### PRIMARY FOCUS: SEARCH-DRIVEN RESEARCH (95% of your work)
Your main job is to SEARCH extensively and gather comprehensive information. Search should be your go-to approach for almost everything.

⚠️ IMP: Total Assistant function-call turns limit: at most ${totalTodos}! You must reach this limit strictly!

For searching:
- PRIORITIZE SEARCH OVER CODE - Search first, search often, search comprehensively
- Do not run all the queries at once, run them one by one, wait for the results before running the next query
- Make 3-5 targeted searches per research topic to get different angles and perspectives
- Search queries should be specific and focused, 5-15 words maximum
- Vary your search approaches: broad overview → specific details → recent developments → expert opinions
- Use different categories strategically: news, research papers, company info, financial reports, github
- Use X search for real-time discussions, public opinion, breaking news, and social media trends
- Follow up initial searches with more targeted queries based on what you learn

Only use code when:
- You need to process or analyze data that was found through searches
- Mathematical calculations are required that cannot be found through search
- Creating visualizations of data trends that were discovered through research

Research Plan:
${JSON.stringify(plan)}`,
  prompt,
  temperature: 0,
  providerOptions: {
    xai: { parallel_tool_calls: 'false' },
  },
  tools: {
    webSearch: { /* Web search implementation */ },
    xSearch: { /* X search implementation */ },
    codeRunner: { /* Code execution implementation */ },
  },
});
```

#### **Research Tools Implementation**

##### **Web Search Tool** (`Lines 411-537`)
```typescript
webSearch: {
  description: 'Search the web for information on a topic',
  inputSchema: z.object({
    query: z.string().describe('The search query to achieve the todo').max(150),
    category: z.nativeEnum(SearchCategory).optional().describe('The category of the search if relevant'),
    includeDomains: z.array(z.string()).optional().describe('The domains to include in the search for results'),
  }),
  execute: async ({ query, category, includeDomains }, { toolCallId }) => {
    console.log('Web search query:', query, 'Category:', category);

    // Stream search start
    if (dataStream) {
      dataStream.write({
        type: 'data-extreme_search',
        data: {
          kind: 'query',
          queryId: toolCallId,
          query: query,
          status: 'started',
        },
      });
    }

    // Execute search
    let results = await searchWeb(query, category, includeDomains);
    console.log(`Found ${results.length} results for query "${query}"`);

    // Add sources to collection
    allSources.push(...results);

    // Stream source discovery
    if (dataStream) {
      results.forEach(async (source) => {
        dataStream.write({
          type: 'data-extreme_search',
          data: {
            kind: 'source',
            queryId: toolCallId,
            source: {
              title: source.title,
              url: source.url,
              favicon: source.favicon,
            },
          },
        });
      });
    }

    // Get full content for results
    if (results.length > 0) {
      if (dataStream) {
        dataStream.write({
          type: 'data-extreme_search',
          data: {
            kind: 'query',
            queryId: toolCallId,
            query: query,
            status: 'reading_content',
          },
        });
      }

      const urls = results.map((r) => r.url);
      const contentsResults = await getContents(urls);

      // Stream content updates
      if (dataStream) {
        contentsResults.forEach((content) => {
          dataStream.write({
            type: 'data-extreme_search',
            data: {
              kind: 'content',
              queryId: toolCallId,
              content: {
                title: content.title || '',
                url: content.url,
                text: (content.content || '').slice(0, 500) + '...',
                favicon: content.favicon || '',
              },
            },
          });
        });
      }

      // Update results with full content
      results = contentsResults.map((content) => {
        const originalResult = results.find((r) => r.url === content.url);
        return {
          title: content.title || originalResult?.title || '',
          url: content.url,
          content: content.content || originalResult?.content || '',
          publishedDate: content.publishedDate || originalResult?.publishedDate || '',
          favicon: content.favicon || originalResult?.favicon || '',
        };
      });
    }

    // Mark query as completed
    if (dataStream) {
      dataStream.write({
        type: 'data-extreme_search',
        data: {
          kind: 'query',
          queryId: toolCallId,
          query: query,
          status: 'completed',
        },
      });
    }

    return results.map((r) => ({
      title: r.title,
      url: r.url,
      content: r.content,
      publishedDate: r.publishedDate,
    }));
  },
}
```

##### **X Search Tool** (`Lines 538-685`)
```typescript
xSearch: {
  description: 'Search X (formerly Twitter) posts for recent information and discussions',
  inputSchema: z.object({
    query: z.string().describe('The search query for X posts').max(150),
    startDate: z.string().describe('The start date in YYYY-MM-DD format (default 7 days ago)').optional(),
    endDate: z.string().describe('The end date in YYYY-MM-DD format (default today)').optional(),
    xHandles: z.array(z.string()).optional().describe('Optional list of X handles to search from'),
    maxResults: z.number().optional().describe('Maximum results (default 15)'),
  }),
  execute: async ({ query, startDate, endDate, xHandles, maxResults = 15 }, { toolCallId }) => {
    console.log('X search query:', query);

    if (dataStream) {
      dataStream.write({
        type: 'data-extreme_search',
        data: {
          kind: 'x_search',
          xSearchId: toolCallId,
          query: query,
          startDate: startDate || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          endDate: endDate || new Date().toISOString().split('T')[0],
          handles: xHandles || [],
          status: 'started',
        },
      });
    }

    try {
      const searchStartDate = startDate || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      const searchEndDate = endDate || new Date().toISOString().split('T')[0];

      const { text, sources } = await generateText({
        model: xai('grok-4-fast-non-reasoning'),
        system: `You are a helpful assistant that searches for X posts and returns the results in a structured format.`,
        messages: [{ role: 'user', content: query }],
        maxOutputTokens: 10,
        providerOptions: {
          xai: {
            searchParameters: {
              mode: 'on',
              fromDate: searchStartDate,
              toDate: searchEndDate,
              maxSearchResults: maxResults < 15 ? 15 : maxResults,
              returnCitations: true,
              sources: [xHandles && xHandles.length > 0 ? { type: 'x', xHandles: xHandles } : { type: 'x' }],
            },
          },
        },
      });

      const citations = sources || [];
      const allSources = [];

      if (citations.length > 0) {
        const tweetFetchPromises = citations
          .filter((link) => link.sourceType === 'url')
          .map(async (link) => {
            try {
              const tweetUrl = link.sourceType === 'url' ? link.url : '';
              const tweetId = tweetUrl.match(/\/status\/(\d+)/)?.[1] || '';

              const tweetData = await getTweet(tweetId);
              if (!tweetData) return null;

              const text = tweetData.text;
              if (!text) return null;

              const userHandle = tweetData.user?.screen_name || tweetData.user?.name || 'unknown';
              const textPreview = text.slice(0, 20) + (text.length > 20 ? '...' : '');
              const generatedTitle = `Post from @${userHandle}: ${textPreview}`;

              return {
                text: text,
                link: tweetUrl,
                title: generatedTitle,
              };
            } catch (error) {
              console.error(`Error fetching tweet data:`, error);
              return null;
            }
          });

        const tweetResults = await Promise.all(tweetFetchPromises);
        allSources.push(...tweetResults.filter((result) => result !== null));
      }

      const result = {
        content: text,
        citations: citations,
        sources: allSources.filter((source): source is { text: string; link: string; title: string } => source !== null),
        dateRange: `${searchStartDate} to ${searchEndDate}`,
        handles: xHandles || [],
      };

      if (dataStream) {
        dataStream.write({
          type: 'data-extreme_search',
          data: {
            kind: 'x_search',
            xSearchId: toolCallId,
            query: query,
            status: 'completed',
            result: result,
          },
        });
      }

      return result;
    } catch (error) {
      console.error('X search error:', error);
      throw error;
    }
  },
}
```

##### **Code Execution Tool** (`Lines 350-410`)
```typescript
codeRunner: {
  description: 'Run Python code in a sandbox',
  inputSchema: z.object({
    title: z.string().describe('The title of what you are running the code for'),
    code: z.string().describe('The Python code to run with proper syntax and imports'),
  }),
  execute: async ({ title, code }) => {
    console.log('Running code:', code);

    // Check for required libraries
    const imports = code.match(/import\s+([\w\s,]+)/);
    const importLibs = imports ? imports[1].split(',').map((lib: string) => lib.trim()) : [];
    const missingLibs = importLibs.filter((lib: string) => !pythonLibsAvailable.includes(lib));

    // Stream code execution start
    if (dataStream) {
      dataStream.write({
        type: 'data-extreme_search',
        data: {
          kind: 'code',
          codeId: `code-${Date.now()}`,
          title: title,
          code: code,
          status: 'running',
        },
      });
    }

    // Execute code in Daytona sandbox
    const response = await runCode(code, missingLibs);

    // Extract chart data, remove PNG for streaming
    const charts = response.artifacts?.charts?.map((chart) => {
      if (chart.png) {
        const { png, ...chartWithoutPng } = chart;
        return chartWithoutPng;
      }
      return chart;
    }) || [];

    // Stream completion
    if (dataStream) {
      dataStream.write({
        type: 'data-extreme_search',
        data: {
          kind: 'code',
          codeId: `code-${Date.now()}`,
          title: title,
          code: code,
          status: 'completed',
          result: response.result,
          charts: charts,
        },
      });
    }

    return {
      result: response.result,
      charts: charts,
    };
  },
}
```

#### **Core Helper Functions**

##### **Web Search Function** (`Lines 77-110`)
```typescript
enum SearchCategory {
  NEWS = 'news',
  COMPANY = 'company',
  RESEARCH_PAPER = 'research paper',
  GITHUB = 'github',
  FINANCIAL_REPORT = 'financial report',
}

const searchWeb = async (query: string, category?: SearchCategory, include_domains?: string[]) => {
  console.log(`searchWeb called with query: "${query}", category: ${category}`);
  try {
    const { results } = await exa.searchAndContents(query, {
      numResults: 8,
      type: 'auto',
      ...(category ? { category: category as SearchCategory } : {}),
      ...(include_domains ? { include_domains: include_domains } : {}),
    });
    console.log(`searchWeb received ${results.length} results from Exa API`);

    const mappedResults = results.map((r) => ({
      title: r.title,
      url: r.url,
      content: r.text,
      publishedDate: r.publishedDate,
      favicon: r.favicon,
    })) as SearchResult[];

    console.log(`searchWeb returning ${mappedResults.length} results`);
    return mappedResults;
  } catch (error) {
    console.error('Error in searchWeb:', error);
    return [];
  }
};
```

##### **Content Retrieval Function** (`Lines 112-190`)
```typescript
const getContents = async (links: string[]) => {
  console.log(`getContents called with ${links.length} URLs:`, links);
  const results: SearchResult[] = [];
  const failedUrls: string[] = [];

  // First, try Exa for all URLs
  try {
    const result = await exa.getContents(links, {
      text: {
        maxCharacters: 3000,
        includeHtmlTags: false,
      },
      livecrawl: 'preferred',
    });
    console.log(`getContents received ${result.results.length} results from Exa API`);

    // Process Exa results
    for (const r of result.results) {
      if (r.text && r.text.trim()) {
        results.push({
          title: r.title || r.url.split('/').pop() || 'Retrieved Content',
          url: r.url,
          content: r.text,
          publishedDate: r.publishedDate || '',
          favicon: r.favicon || `https://www.google.com/s2/favicons?domain=${new URL(r.url).hostname}&sz=128`,
        });
      } else {
        failedUrls.push(r.url);
      }
    }

    // Add any URLs that weren't returned by Exa to the failed list
    const exaUrls = result.results.map((r) => r.url);
    const missingUrls = links.filter((url) => !exaUrls.includes(url));
    failedUrls.push(...missingUrls);
  } catch (error) {
    console.error('Exa API error:', error);
    failedUrls.push(...links);
  }

  // Use Firecrawl as fallback for failed URLs
  if (failedUrls.length > 0) {
    console.log(`Using Firecrawl fallback for ${failedUrls.length} URLs:`, failedUrls);

    for (const url of failedUrls) {
      try {
        const scrapeResponse = await firecrawl.scrape(url, {
          formats: ['markdown'],
          proxy: 'auto',
          storeInCache: true,
          parsers: ['pdf'],
        });

        if (scrapeResponse.markdown) {
          console.log(`Firecrawl successfully scraped ${url}`);

          results.push({
            title: scrapeResponse.metadata?.title || url.split('/').pop() || 'Retrieved Content',
            url: url,
            content: scrapeResponse.markdown.slice(0, 3000),
            publishedDate: (scrapeResponse.metadata?.publishedDate as string) || '',
            favicon: `https://www.google.com/s2/favicons?domain=${new URL(url).hostname}&sz=128`,
          });
        } else {
          console.error(`Firecrawl failed for ${url}:`, scrapeResponse);
        }
      } catch (firecrawlError) {
        console.error(`Firecrawl error for ${url}:`, firecrawlError);
      }
    }
  }

  console.log(`getContents returning ${results.length} total results`);
  return results;
};
```

##### **Code Execution Function** (`Lines 37-49`)
```typescript
const runCode = async (code: string, installLibs: string[] = []) => {
  const sandbox = await daytona.create({
    snapshot: SNAPSHOT_NAME,
  });

  if (installLibs.length > 0) {
    await sandbox.process.executeCommand(`pip install ${installLibs.join(' ')}`);
  }

  const result = await sandbox.process.codeRun(code);
  sandbox.delete();
  return result;
};
```

#### **Tool Registration and Export** (`Lines 733-758`)
```typescript
export function extremeSearchTool(dataStream: UIMessageStreamWriter<ChatMessage> | undefined) {
  return tool({
    description: 'Use this tool to conduct an extreme search on a given topic.',
    inputSchema: z.object({
      prompt: z.string().describe("This should take the user's exact prompt. Extract from the context but do not infer or change in any way."),
    }),
    execute: async ({ prompt }) => {
      console.log({ prompt });

      const research = await extremeSearch(prompt, dataStream);

      return {
        research: {
          text: research.text,
          toolResults: research.toolResults,
          sources: research.sources,
          charts: research.charts,
        },
      };
    },
  });
}
```

---

## Content Processing Pipeline

### **Real-Time Processing Architecture**

The content processing happens **during search execution**, not at the end. Here's the complete flow:

#### **1. Immediate Search Execution**
```typescript
// extreme-search.ts:418-437
webSearch: {
  execute: async ({ query, category, includeDomains }, { toolCallId }) => {
    // Stream search start
    dataStream?.write({
      type: 'data-extreme_search',
      kind: 'query',
      status: 'started',
    });

    // Execute search immediately
    let results = await searchWeb(query, category, includeDomains);

    // Process results right away
    allSources.push(...results);
  }
}
```

#### **2. Content Retrieval with Fallback**
```typescript
// extreme-search.ts:456-515
if (results.length > 0) {
  // Stream content reading status
  dataStream?.write({
    type: 'data-extreme_search',
    kind: 'query',
    status: 'reading_content',
  });

  const urls = results.map((r) => r.url);
  const contentsResults = await getContents(urls);

  // Stream individual content pieces
  if (dataStream) {
    contentsResults.forEach((content) => {
      dataStream.write({
        type: 'data-extreme_search',
        kind: 'content',
        content: {
          title: content.title || '',
          url: content.url,
          text: (content.content || '').slice(0, 500) + '...',
          favicon: content.favicon || '',
        },
      });
    });
  }
}
```

#### **3. Multi-Provider Content Processing**
```typescript
// web-search.ts:117-152
const searchPromises = limitedQueries.map(async (query, index) => {
  // Parallel execution of search and image collection
  const [singleResponse, firecrawlImages] = await Promise.all([
    this.parallel.beta.search(searchParams),
    this.firecrawl.search(query, { sources: ['images'], limit: 3 }),
  ]);

  // Immediate content processing
  const results = (singleResponse?.results || []).map((result: any) => ({
    url: result.url,
    title: cleanTitle(result.title || ''),
    content: Array.isArray(result.excerpts)
      ? result.excerpts.join(' ').substring(0, 1000)
      : (result.content || '').substring(0, 1000),
  }));

  // Stream completion immediately
  options.dataStream?.write({
    type: 'data-query_completion',
    data: { query, index, status: 'completed', resultsCount: results.length },
  });

  return { query, results, images: firecrawlImages.images || [] };
});
```

#### **4. Content Deduplication and Enhancement**
```typescript
// web-search.ts:26-42
const deduplicateByDomainAndUrl = <T extends { url: string }>(items: T[]): T[] => {
  const seenDomains = new Set<string>();
  const seenUrls = new Set<string>();

  return items.filter((item) => {
    const domain = extractDomain(item.url);
    const isNewUrl = !seenUrls.has(item.url);
    const isNewDomain = !seenDomains.has(domain);

    if (isNewUrl && isNewDomain) {
      seenUrls.add(item.url);
      seenDomains.add(domain);
      return true;
    }
    return false;
  });
};

// extreme-search.ts:726-729
sources: Array.from(
  new Map(allSources.map((s) => [s.url, { ...s, content: s.content.slice(0, 3000) + '...' }])).values(),
),
```

#### **5. Progressive Content Enhancement**
```typescript
// extreme-search.ts:497-508
results = contentsResults.map((content) => {
  const originalResult = results.find((r) => r.url === content.url);
  return {
    title: content.title || originalResult?.title || '',
    url: content.url,
    content: content.content || originalResult?.content || '',
    publishedDate: content.publishedDate || originalResult?.publishedDate || '',
    favicon: content.favicon || originalResult?.favicon || '',
  };
});
```

### **Content Quality Processing**

#### **Title Cleaning**
```typescript
// web-search.ts:17-24
const cleanTitle = (title: string): string => {
  return title
    .replace(/\[.*?\]/g, '') // Remove [content]
    .replace(/\(.*?\)/g, '') // Remove (content)
    .replace(/\s+/g, ' ') // Replace multiple spaces with single space
    .trim(); // Remove leading/trailing whitespace
};
```

#### **Image URL Validation**
```typescript
// web-search.ts:72-89
const sanitizeUrl = (url: string): string => {
  try {
    const urlObj = new URL(url);
    return urlObj.href;
  } catch {
    return url;
  }
};

const isValidImageUrl = async (url: string): Promise<{ valid: boolean; redirectedUrl?: string }> => {
  try {
    return { valid: true, redirectedUrl: sanitizeUrl(url) };
  } catch {
    return { valid: false };
  }
};
```

#### **Content Length Management**
```typescript
// extreme-search.ts:121-124
text: {
  maxCharacters: 3000,
  includeHtmlTags: false,
},

// extreme-search.ts:173
content: scrapeResponse.markdown.slice(0, 3000),
```

---

## Supermemory Integration

### **Memory Tools Creation**: `lib/tools/supermemory.ts:1-44`

```typescript
import { supermemoryTools } from '@supermemory/tools/ai-sdk';
import { Tool } from 'ai';
import { serverEnv } from '@/env/server';

export function createMemoryTools(userId: string) {
  return supermemoryTools(serverEnv.SUPERMEMORY_API_KEY, {
    containerTags: [userId],
  });
}

export type SearchMemoryTool = Tool<
  {
    informationToGet: string;
  },
  | {
      success: boolean;
      results: any[];
      count: number;
      error?: undefined;
    }
  | {
      success: boolean;
      error: string;
      results?: undefined;
      count?: undefined;
    }
>;

export type AddMemoryTool = Tool<
  {
    memory: string;
  },
  | {
      success: boolean;
      memory: any;
      error?: undefined;
    }
  | {
      success: boolean;
      error: string;
      memory?: undefined;
    }
>;
```

### **Memory Actions**: `lib/memory-actions.ts:1-118`

```typescript
'use server';

import { getUser } from '@/lib/auth-utils';
import { serverEnv } from '@/env/server';
import { Supermemory } from 'supermemory';

const supermemoryClient = new Supermemory({
  apiKey: serverEnv.SUPERMEMORY_API_KEY
});

export interface MemoryItem {
  id: string;
  customId: string;
  connectionId: string | null;
  containerTags: string[];
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, any>;
  status: string;
  summary: string;
  title: string;
  type: string;
  content: string;
  // Legacy fields for backward compatibility
  name?: string;
  memory?: string;
  user_id?: string;
  owner?: string;
}

export interface MemoryResponse {
  memories: MemoryItem[];
  total: number;
}

/**
 * Search memories for the authenticated user
 */
export async function searchMemories(query: string, page = 1, pageSize = 20): Promise<MemoryResponse> {
  const user = await getUser();

  if (!user) {
    throw new Error('Authentication required');
  }

  if (!query.trim()) {
    return { memories: [], total: 0 };
  }

  try {
    const result = await supermemoryClient.search.memories({
      q: query,
      containerTag: user.id,
      limit: pageSize,
    });

    // Return empty results for now - implementation incomplete
    return { memories: [], total: result.total || 0 };
  } catch (error) {
    console.error('Error searching memories:', error);
    throw error;
  }
}

/**
 * Get all memories for the authenticated user
 */
export async function getAllMemories(page = 1, pageSize = 20): Promise<MemoryResponse> {
  const user = await getUser();

  if (!user) {
    throw new Error('Authentication required');
  }

  try {
    const result = await supermemoryClient.memories.list({
      containerTags: [user.id],
      page: page,
      limit: pageSize,
      includeContent: true,
    });

    return {
      memories: result.memories as any,
      total: result.pagination.totalItems || 0,
    };
  } catch (error) {
    console.error('Error fetching memories:', error);
    throw error;
  }
}

/**
 * Delete a memory by ID
 */
export async function deleteMemory(memoryId: string) {
  const user = await getUser();

  if (!user) {
    throw new Error('Authentication required');
  }

  try {
    const data = await supermemoryClient.memories.delete(memoryId);
    return data;
  } catch (error) {
    console.error('Error deleting memory:', error);
    throw error;
  }
}
```

### **Memory Integration in Search API**
```typescript
// app/api/search/route.ts:521-527
if (!user) {
  return baseTools;
}

const memoryTools = createMemoryTools(user.id);
return {
  ...baseTools,
  search_memories: memoryTools.searchMemories as any,
  add_memory: memoryTools.addMemory as any,
  connectors_search: createConnectorsSearchTool(user.id, selectedConnectors),
} as any;
```

---

## Document Connectors Integration

### **Connectors Search Tool**: `lib/tools/connectors-search.ts:1-313`

```typescript
import { tool } from 'ai';
import { z } from 'zod';
import Supermemory from 'supermemory';
import { CONNECTOR_CONFIGS, type ConnectorProvider, type ConnectorConfig } from '@/lib/connectors';

// Type definitions for Supermemory documents
interface DocumentChunk {
  content: string;
  score?: number;
  metadata?: Record<string, unknown>;
}

interface SupermemoryDocument {
  documentId: string;
  title?: string;
  content?: string;
  summary?: string;
  chunks?: DocumentChunk[];
  score?: number;
  metadata?: DocumentMetadata;
}

interface EnhancedDocument {
  documentId: string;
  title: string | null;
  content: string | null;
  summary: string | null;
  chunks: Array<{
    content: string;
    score: number;
    isRelevant: boolean;
  }>;
  score: number;
  metadata: Record<string, unknown> | null;
  provider: ConnectorProvider | null;
  providerConfig: ConnectorConfig | null;
  url: string;
  type: string | null;
  createdAt: string;
  updatedAt: string;
}

const client = new Supermemory({
  apiKey: process.env.SUPERMEMORY_API_KEY!
});

export function createConnectorsSearchTool(userId: string, selectedConnectors?: ConnectorProvider[]) {
  // Create dynamic provider enum based on selected connectors
  const availableProviders = selectedConnectors && selectedConnectors.length > 0
    ? [...selectedConnectors, 'all']
    : [...Object.keys(CONNECTOR_CONFIGS) as ConnectorProvider[], 'all'];

  return tool({
    description: "Search for documents in the user's connected services (Google Drive, Notion, OneDrive)",
    inputSchema: z.object({
      query: z.string().describe('The search query to find relevant documents'),
      provider: z.enum(availableProviders as [ConnectorProvider | 'all', ...(ConnectorProvider | 'all')[]]).optional().describe('Specific provider to search in, or "all" for all connected services'),
    }),
    execute: async ({ query, provider = 'all' }): Promise<SearchResponse> => {
      console.log('🔍 [ConnectorsSearch] Starting search with params:', { query, provider, userId });

      try {
        let allResults: SupermemoryDocument[] = [];
        let totalCount = 0;

        if (provider === 'all') {
          // Use selected connectors if available, otherwise search all
          const providersToSearch = selectedConnectors && selectedConnectors.length > 0
            ? selectedConnectors
            : Object.keys(CONNECTOR_CONFIGS) as ConnectorProvider[];

          // Search each provider separately and combine results
          const searchPromises = providersToSearch.map(async (providerKey): Promise<SupermemorySearchResult> => {
            try {
              const config = CONNECTOR_CONFIGS[providerKey];
              console.log(`🔎 [ConnectorsSearch] Searching ${providerKey} with tags:`, [userId, config.syncTag]);

              const result = await client.search.documents({
                q: query,
                containerTags: [userId, config.syncTag],
                limit: 15,
                rerank: true,
                includeSummary: true,
              });

              console.log(`✅ [ConnectorsSearch] ${providerKey} returned ${result.results?.length || 0} results`);
              return result as SupermemorySearchResult;
            } catch (error) {
              console.error(`❌ [ConnectorsSearch] Error searching ${providerKey}:`, error);
              return { results: [], total: 0 };
            }
          });

          const searchResults = await Promise.all(searchPromises);

          // Combine all results
          allResults = searchResults.flatMap(result => result.results || []);
          totalCount = searchResults.reduce((sum, result) => sum + (result.total || 0), 0);
        } else {
          // Search specific provider
          const config = CONNECTOR_CONFIGS[provider as ConnectorProvider];
          const result = await client.search.documents({
            q: query,
            containerTags: [userId, config.syncTag],
            limit: 15,
            rerank: true,
            includeSummary: true,
            includeFullDocs: true,
          }) as SupermemorySearchResult;

          allResults = result.results || [];
          totalCount = result.total || 0;
        }

        // Document URL generation based on provider
        const generateDocumentUrl = (document: SupermemoryDocument, provider: ConnectorProvider | null): string => {
          if (!provider) return '#';

          const providerLower = provider.toLowerCase();

          switch (providerLower) {
            case 'google_drive':
            case 'google-drive':
              return `https://drive.google.com/file/d/${document.documentId}/view`;
            case 'onedrive':
              return `https://1drv.ms/b/s!${document.documentId}`;
            case 'notion':
              const title = document.title || 'untitled';
              const filenameWithHyphens = title
                .toLowerCase()
                .replace(/[^a-z0-9\s-]/g, '')
                .replace(/\s+/g, '-')
                .replace(/-+/g, '-')
                .replace(/^-|-$/g, '');
              const docIdWithoutHyphens = document.documentId.replace(/-/g, '');
              return `https://notion.so/${filenameWithHyphens}-${docIdWithoutHyphens}`;
            default:
              return '#';
          }
        };

        // Content validation
        const hasValidContent = (doc: SupermemoryDocument): boolean => {
          if (doc.chunks && Array.isArray(doc.chunks)) {
            const hasValidChunks = doc.chunks.some((chunk: DocumentChunk) =>
              chunk.content &&
              chunk.content.trim() !== '' &&
              chunk.content !== 'Empty Chunk'
            );
            if (hasValidChunks) return true;
          }

          if (doc.summary && doc.summary.trim() !== '' && doc.summary !== 'Empty Chunk') {
            return true;
          }

          if (doc.content && doc.content.trim() !== '' && doc.content !== 'Empty Chunk') {
            return true;
          }

          return false;
        };

        // Filter invalid documents
        const validResults = allResults.filter(hasValidContent);

        // Enhance results with provider information
        const enhancedResults: EnhancedDocument[] = validResults.map((doc): EnhancedDocument => {
          // Detect provider from metadata or tags
          let detectedProvider: ConnectorProvider | null = null;

          if (doc.metadata?.source) {
            detectedProvider = doc.metadata.source as ConnectorProvider;
          } else if (doc.metadata?.containerTags) {
            const docTags = Array.isArray(doc.metadata.containerTags)
              ? doc.metadata.containerTags
              : [doc.metadata.containerTags];

            for (const [providerKey, config] of Object.entries(CONNECTOR_CONFIGS)) {
              if (docTags.includes(config.syncTag)) {
                detectedProvider = providerKey as ConnectorProvider;
                break;
              }
            }
          }

          const documentUrl = generateDocumentUrl(doc, detectedProvider);
          const now = new Date().toISOString();
          const createdAt = (doc.metadata?.createdAt as string) || now;
          const updatedAt = (doc.metadata?.updatedAt as string) || now;
          const type = (doc.metadata?.type as string) || (doc.metadata?.mimeType as string) || 'document';

          // Transform chunks
          const chunks = (doc.chunks || []).map((chunk) => ({
            content: chunk.content,
            score: chunk.score || 0,
            isRelevant: (chunk.score || 0) > 0.5,
          }));

          return {
            documentId: doc.documentId,
            title: doc.title || null,
            content: doc.content || null,
            summary: doc.summary || null,
            chunks,
            score: doc.score || 0,
            metadata: doc.metadata || null,
            provider: detectedProvider,
            providerConfig: detectedProvider ? CONNECTOR_CONFIGS[detectedProvider] : null,
            url: documentUrl,
            type,
            createdAt,
            updatedAt,
          };
        });

        // Sort by score
        enhancedResults.sort((a, b) => (b.score || 0) - (a.score || 0));

        const response: SearchSuccessResponse = {
          success: true,
          results: enhancedResults,
          count: enhancedResults.length,
          query,
          provider: provider === 'all' ? 'all connected services' : CONNECTOR_CONFIGS[provider as ConnectorProvider]?.name || provider,
        };

        console.log(`🎉 [ConnectorsSearch] Search complete! Returning ${enhancedResults.length} results`);
        return response;
      } catch (error) {
        console.error('❌ [ConnectorsSearch] Error searching connectors:', error);

        const errorResponse: SearchErrorResponse = {
          success: false,
          error: 'Failed to search your connected documents',
          provider: provider === 'all' ? 'all connected services' : CONNECTOR_CONFIGS[provider as ConnectorProvider]?.name || provider,
        };
        return errorResponse;
      }
    },
  });
}
```

---

## Real-Time Streaming Architecture

### **Stream Event Types**

The system uses multiple event types for real-time progress updates:

#### **Extreme Search Events**
```typescript
// Research planning
{
  type: 'data-extreme_search',
  data: {
    kind: 'plan',
    status: { title: 'Planning research' },
    plan: [...],  // When plan is ready
  }
}

// Query execution
{
  type: 'data-extreme_search',
  data: {
    kind: 'query',
    queryId: toolCallId,
    query: string,
    status: 'started' | 'reading_content' | 'completed' | 'error',
  }
}

// Source discovery
{
  type: 'data-extreme_search',
  data: {
    kind: 'source',
    queryId: toolCallId,
    source: {
      title: string,
      url: string,
      favicon: string,
    },
  }
}

// Content retrieval
{
  type: 'data-extreme_search',
  data: {
    kind: 'content',
    queryId: toolCallId,
    content: {
      title: string,
      url: string,
      text: string,  // Content preview
      favicon: string,
    },
  }
}

// Code execution
{
  type: 'data-extreme_search',
  data: {
    kind: 'code',
    codeId: string,
    title: string,
    code: string,
    status: 'running' | 'completed' | 'error',
    result?: string,
    charts?: ChartData[],
  }
}

// X search
{
  type: 'data-extreme_search',
  data: {
    kind: 'x_search',
    xSearchId: string,
    query: string,
    startDate: string,
    endDate: string,
    handles: string[],
    status: 'started' | 'completed' | 'error',
    result?: XSearchResult,
  }
}
```

#### **Web Search Query Completion Events**
```typescript
{
  type: 'data-query_completion',
  data: {
    query: string,
    index: number,
    total: number,
    status: 'started' | 'completed' | 'error',
    resultsCount: number,
    imagesCount: number,
  }
}
```

### **Streaming Implementation**

#### **Main Stream Setup**: `app/api/search/route.ts:287-661`
```typescript
const stream = createUIMessageStream<ChatMessage>({
  execute: async ({ writer: dataStream }) => {
    // Stream configuration
    const result = streamText({
      model: scira.languageModel(model),
      messages: convertToModelMessages(messages),
      activeTools: [...activeTools],

      onChunk(event) {
        if (event.chunk.type === 'tool-call') {
          console.log('Called Tool: ', event.chunk.toolName);
        }
      },

      onStepFinish(event) {
        console.log('Step Request:', event.request);
        if (event.warnings) {
          console.log('Warnings: ', event.warnings);
        }
      },

      onFinish: async (event) => {
        const processingTime = (Date.now() - requestStartTime) / 1000;
        console.log(`✅ Request completed: ${processingTime.toFixed(2)}s (${event.finishReason})`);

        // Track usage in background
        if (user?.id && event.finishReason === 'stop') {
          after(async () => {
            if (!shouldBypassRateLimits(model, user)) {
              await incrementMessageUsage({ userId: user.id });
            }

            if (group === 'extreme') {
              const extremeSearchUsed = event.steps?.some((step) =>
                step.toolCalls?.some((toolCall) => toolCall.toolName === 'extreme_search'),
              );
              if (extremeSearchUsed) {
                await incrementExtremeSearchUsage({ userId: user.id });
              }
            }
          });
        }
      },

      onError(event) {
        const processingTime = (Date.now() - requestStartTime) / 1000;
        console.error(`❌ Request failed: ${processingTime.toFixed(2)}s`, event.error);
      },
    });

    result.consumeStream();

    // Merge with user-facing stream
    dataStream.merge(
      result.toUIMessageStream({
        sendReasoning: true,
        messageMetadata: ({ part }) => {
          if (part.type === 'finish') {
            const processingTime = (Date.now() - streamStartTime) / 1000;
            return {
              model: model as string,
              completionTime: processingTime,
              createdAt: new Date().toISOString(),
              totalTokens: part.totalUsage?.totalTokens ?? null,
              inputTokens: part.totalUsage?.inputTokens ?? null,
              outputTokens: part.totalUsage?.outputTokens ?? null,
            };
          }
        },
      }),
    );
  },
  onError(error) {
    console.log('Error: ', error);
    if (error instanceof Error && error.message.includes('Rate Limit')) {
      return 'Oops, you have reached the rate limit! Please try again later.';
    }
    return 'Oops, an error occurred!';
  },
  onFinish: async ({ messages }) => {
    // Save messages to database
    if (lightweightUser) {
      await saveMessages({
        messages: messages.map((message) => ({
          id: message.id,
          role: message.role,
          parts: message.parts,
          createdAt: new Date(),
          chatId: id,
          model: model,
          completionTime: message.metadata?.completionTime ?? 0,
          inputTokens: message.metadata?.inputTokens ?? 0,
          outputTokens: message.metadata?.outputTokens ?? 0,
          totalTokens: message.metadata?.totalTokens ?? 0,
        })),
      });
    }
  },
});

return new Response(stream.pipeThrough(new JsonToSseTransformStream()));
```

#### **Tool-Specific Streaming Examples**

##### **Web Search Streaming**: `lib/tools/web-search.ts:124-192`
```typescript
// Parallel search with streaming
const perQueryPromises = limitedQueries.map(async (query, index) => {
  // Send start notification
  options.dataStream?.write({
    type: 'data-query_completion',
    data: {
      query,
      index,
      total: limitedQueries.length,
      status: 'started',
      resultsCount: 0,
      imagesCount: 0,
    },
  });

  try {
    const [singleResponse, firecrawlImages] = await Promise.all([
      this.parallel.beta.search(searchParams),
      this.firecrawl.search(query, { sources: ['images'], limit: 3 }),
    ]);

    // Send completion notification
    options.dataStream?.write({
      type: 'data-query_completion',
      data: {
        query,
        index,
        total: limitedQueries.length,
        status: 'completed',
        resultsCount: results.length,
        imagesCount: images.length,
      },
    });

    return { query, results, images };
  } catch (error) {
    // Send error notification
    options.dataStream?.write({
      type: 'data-query_completion',
      data: {
        query,
        index,
        total: limitedQueries.length,
        status: 'error',
        resultsCount: 0,
        imagesCount: 0,
      },
    });

    return { query, results: [], images: [] };
  }
});
```

##### **Extreme Search Progress Streaming**: `lib/tools/extreme-search.ts:422-527`
```typescript
// Multi-stage streaming for research progress
if (dataStream) {
  // Search started
  dataStream.write({
    type: 'data-extreme_search',
    data: {
      kind: 'query',
      queryId: toolCallId,
      query: query,
      status: 'started',
    },
  });

  // Reading content
  dataStream.write({
    type: 'data-extreme_search',
    data: {
      kind: 'query',
      queryId: toolCallId,
      query: query,
      status: 'reading_content',
    },
  });

  // Individual sources
  results.forEach(async (source) => {
    dataStream.write({
      type: 'data-extreme_search',
      data: {
        kind: 'source',
        queryId: toolCallId,
        source: {
          title: source.title,
          url: source.url,
          favicon: source.favicon,
        },
      },
    });
  });

  // Content pieces
  contentsResults.forEach((content) => {
    dataStream.write({
      type: 'data-extreme_search',
      data: {
        kind: 'content',
        queryId: toolCallId,
        content: {
          title: content.title || '',
          url: content.url,
          text: (content.content || '').slice(0, 500) + '...',
          favicon: content.favicon || '',
        },
      },
    });
  });

  // Search completed
  dataStream.write({
    type: 'data-extreme_search',
    data: {
      kind: 'query',
      queryId: toolCallId,
      query: query,
      status: 'completed',
    },
  });
}
```

---

## Authentication & Rate Limiting

### **Authentication System**

#### **User Authentication Flow**: `app/api/search/route.ts:125-155`
```typescript
// CRITICAL PATH: Get auth status first (required for all subsequent checks)
const lightweightUser = await getLightweightUser();

// Rate limit check for unauthenticated users
if (!lightweightUser) {
  const identifier = getClientIdentifier(req);
  const { success, limit, reset } = await unauthenticatedRateLimit.limit(identifier);

  if (!success) {
    const resetDate = new Date(reset);
    return new ChatSDKError(
      'rate_limit:api',
      `You've reached the limit of ${limit} searches per day for unauthenticated users. Sign in for more searches or wait until ${resetDate.toLocaleString()}.`
    ).toResponse();
  }
}

// Early exit checks (no DB operations needed)
if (!lightweightUser) {
  if (requiresAuthentication(model)) {
    return new ChatSDKError('unauthorized:model', `${model} requires authentication`).toResponse();
  }
  if (group === 'extreme') {
    return new ChatSDKError('unauthorized:auth', 'Authentication required to use Extreme Search mode').toResponse();
  }
} else {
  // Fast auth checks using lightweight user (no additional DB calls)
  if (requiresProSubscription(model) && !lightweightUser.isProUser) {
    return new ChatSDKError('upgrade_required:model', `${model} requires a Pro subscription`).toResponse();
  }
}
```

#### **Authentication Requirements**
```typescript
// AI provider requirements
function requiresAuthentication(model: string): boolean {
  const authRequiredModels = [
    'scira-gpt5', 'scira-o3', 'scira-gpt-4.1',
    'scira-anthropic-think', 'scira-google-think',
    // ... other premium models
  ];
  return authRequiredModels.includes(model);
}

// Pro subscription requirements
function requiresProSubscription(model: string): boolean {
  const proOnlyModels = [
    'scira-gpt5', 'scira-o3', 'scira-gpt5-codex',
    'scira-gpt5-medium', 'scira-o4-mini',
    // ... other pro models
  ];
  return proOnlyModels.includes(model);
}
```

### **Rate Limiting Implementation**

#### **Rate Limiting Tiers**
- **Unauthenticated**: 100 searches/day
- **Authenticated (Free)**: 1000 searches/hour, 100 searches/day total
- **Pro Users**: Unlimited searches
- **Extreme Search**: Authentication required

#### **Rate Limiting Logic**: `app/api/search/route.ts:218-271`
```typescript
// For non-Pro users: run usage checks in parallel
if (!isProUser) {
  criticalChecksPromise = Promise.all([
    fullUserPromise,
    chatValidationPromise,
  ]).then(async ([user]) => {
    if (!user) {
      throw new ChatSDKError('unauthorized:auth', 'User authentication failed');
    }

    const [messageCountResult, extremeSearchUsage] = await Promise.all([
      getUserMessageCount(user),
      getExtremeSearchUsageCount(user),
    ]);

    if (messageCountResult.error) {
      throw new ChatSDKError('bad_request:api', 'Failed to verify usage limits');
    }

    const shouldBypassLimits = shouldBypassRateLimits(model, user);
    if (!shouldBypassLimits && messageCountResult.count !== undefined && messageCountResult.count >= 100) {
      throw new ChatSDKError('rate_limit:chat', 'Daily search limit reached');
    }

    return {
      canProceed: true,
      isProUser: false,
      messageCount: messageCountResult.count,
      extremeSearchUsage: extremeSearchUsage.count,
      subscriptionData: user.polarSubscription
        ? { hasSubscription: true, subscription: { ...user.polarSubscription, organizationId: null } }
        : { hasSubscription: false },
      shouldBypassLimits,
    };
  });
}
```

#### **Rate Limiting Configuration**
```typescript
// lib/rate-limit.ts (example structure)
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

export const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

export const unauthenticatedRateLimit = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(100, '1 d'), // 100 requests per day
  analytics: true,
});

export const authenticatedRateLimit = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(1000, '1 h'), // 1000 requests per hour
  analytics: true,
});
```

#### **Client Identification**
```typescript
// lib/rate-limit.ts
export function getClientIdentifier(req: Request): string {
  // Try to get IP address from various headers
  const forwarded = req.headers.get('x-forwarded-for');
  const realIp = req.headers.get('x-real-ip');
  const ip = forwarded?.split(',')[0] || realIp || 'unknown';

  // Add user agent for better identification
  const userAgent = req.headers.get('user-agent') || 'unknown';

  return `${ip}:${Buffer.from(userAgent).toString('base64').slice(0, 16)}`;
}
```

### **Usage Tracking**

#### **Message Usage Tracking**: `app/api/search/route.ts:586-605`
```typescript
onFinish: async (event) => {
  if (user?.id && event.finishReason === 'stop') {
    // Track usage in background
    after(async () => {
      try {
        if (!shouldBypassRateLimits(model, user)) {
          await incrementMessageUsage({ userId: user.id });
        }

        // Track extreme search usage if used
        if (group === 'extreme') {
          const extremeSearchUsed = event.steps?.some((step) =>
            step.toolCalls?.some((toolCall) => toolCall.toolName === 'extreme_search'),
          );
          if (extremeSearchUsed) {
            await incrementExtremeSearchUsage({ userId: user.id });
          }
        }
      } catch (error) {
        console.error('Failed to track usage:', error);
      }
    });
  }
},
```

---

## Database Schema & Performance

### **Database Schema**: `lib/db/schema.ts`

#### **Core Tables Structure**
```typescript
// User Management
export const user = pgTable('user', {
  id: text('id').primaryKey(),
  email: text('email').unique().notNull(),
  name: text('name'),
  emailVerified: boolean('email_verified').default(false),
  image: text('image'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

export const session = pgTable('session', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  token: text('token').unique().notNull(),
  expiresAt: timestamp('expires_at').notNull(),
  createdAt: timestamp('created_at').defaultNow(),
});

export const account = pgTable('account', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  type: text('type').notNull(),
  provider: text('provider').notNull(),
  providerAccountId: text('provider_account_id').notNull(),
  refreshToken: text('refresh_token'),
  accessToken: text('access_token'),
  expiresAt: timestamp('expires_at'),
  tokenType: text('token_type'),
  scope: text('scope'),
  idToken: text('id_token'),
  sessionState: text('session_state'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

// Chat Functionality
export const chat = pgTable('chat', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  title: text('title').notNull(),
  visibility: text('visibility', { enum: ['public', 'private', 'unlisted'] }).default('private'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

export const message = pgTable('message', {
  id: text('id').primaryKey(),
  chatId: text('chat_id').references(() => chat.id, { onDelete: 'cascade' }).notNull(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  role: text('role', { enum: ['user', 'assistant', 'system'] }).notNull(),
  parts: json('parts').notNull(),
  attachments: json('attachments').$type<Attachment[]>(),
  createdAt: timestamp('created_at').defaultNow(),
  model: text('model'),
  inputTokens: integer('input_tokens').default(0),
  outputTokens: integer('output_tokens').default(0),
  totalTokens: integer('total_tokens').default(0),
  completionTime: real('completion_time').default(0),
});

export const stream = pgTable('stream', {
  id: text('id').primaryKey(),
  chatId: text('chat_id').references(() => chat.id, { onDelete: 'cascade' }).notNull(),
  createdAt: timestamp('created_at').defaultNow(),
});

// Usage Tracking
export const extremeSearchUsage = pgTable('extreme_search_usage', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  date: timestamp('date').defaultNow(),
  usageCount: integer('usage_count').default(0),
  createdAt: timestamp('created_at').defaultNow(),
});

export const messageUsage = pgTable('message_usage', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  date: timestamp('date').defaultNow(),
  messageCount: integer('message_count').default(0),
  createdAt: timestamp('created_at').defaultNow(),
});

// Monetization
export const subscription = pgTable('subscription', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  polarSubscriptionId: text('polar_subscription_id').unique(),
  status: text('status').notNull(),
  productId: text('product_id').notNull(),
  amount: integer('amount').notNull(),
  currency: text('currency').notNull(),
  interval: text('interval').notNull(),
  currentPeriodStart: timestamp('current_period_start').notNull(),
  currentPeriodEnd: timestamp('current_period_end').notNull(),
  canceledAt: timestamp('canceled_at'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

export const payment = pgTable('payment', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  polarPaymentId: text('polar_payment_id').unique(),
  subscriptionId: text('subscription_id').references(() => subscription.id, { onDelete: 'cascade' }),
  amount: integer('amount').notNull(),
  currency: text('currency').notNull(),
  status: text('status').notNull(),
  paymentMethod: text('payment_method'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

// Features
export const customInstructions = pgTable('custom_instructions', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  content: text('content').notNull(),
  isActive: boolean('is_active').default(true),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

export const lookout = pgTable('lookout', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => user.id, { onDelete: 'cascade' }).notNull(),
  query: text('query').notNull(),
  frequency: text('frequency', { enum: ['once', 'daily', 'weekly', 'monthly', 'yearly'] }).notNull(),
  cronExpression: text('cron_expression'),
  lastRunAt: timestamp('last_run_at'),
  nextRunAt: timestamp('next_run_at'),
  isActive: boolean('is_active').default(true),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});
```

### **Database Performance Optimization**: `create_indexes.sql`

#### **27 Optimized Indexes**
```sql
-- User and Authentication Indexes
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_created_at ON user(created_at);
CREATE INDEX idx_session_user_expires ON session(user_id, expires_at);
CREATE INDEX idx_session_token ON session(token);
CREATE INDEX idx_account_user_id ON account(user_id);
CREATE INDEX idx_account_provider ON account(provider, provider_account_id);

-- Chat and Message Indexes
CREATE INDEX idx_chat_user_id ON chat(user_id);
CREATE INDEX idx_chat_created_at ON chat(created_at);
CREATE INDEX idx_chat_user_created ON chat(user_id, created_at);
CREATE INDEX idx_message_chat_id ON message(chat_id);
CREATE INDEX idx_message_user_id ON message(user_id);
CREATE INDEX idx_message_created_at ON message(created_at);
CREATE INDEX idx_message_chat_created ON message(chat_id, created_at);
CREATE INDEX idx_message_user_chat_order ON message(user_id, chat_id, created_at);
CREATE INDEX idx_stream_chat_id ON stream(chat_id);

-- Usage Tracking Indexes
CREATE INDEX idx_extreme_search_usage_user_date ON extreme_search_usage(user_id, date);
CREATE INDEX idx_extreme_search_usage_date ON extreme_search_usage(date);
CREATE INDEX idx_message_usage_user_date ON message_usage(user_id, date);
CREATE INDEX idx_message_usage_date ON message_usage(date);

-- Subscription and Payment Indexes
CREATE INDEX idx_subscription_user_id ON subscription(user_id);
CREATE INDEX idx_subscription_polar_id ON subscription(polar_subscription_id);
CREATE INDEX idx_subscription_status ON subscription(status);
CREATE INDEX idx_payment_user_id ON payment(user_id);
CREATE INDEX idx_payment_subscription_id ON payment(subscription_id);
CREATE INDEX idx_payment_polar_id ON payment(polar_payment_id);

-- Feature Indexes
CREATE INDEX idx_custom_instructions_user_id ON custom_instructions(user_id);
CREATE INDEX idx_custom_instructions_active ON custom_instructions(is_active);
CREATE INDEX idx_lookout_user_id ON lookout(user_id);
CREATE INDEX idx_lookout_next_run ON lookout(next_run_at);
CREATE INDEX idx_lookout_active ON lookout(is_active);
CREATE INDEX idx_verification_token ON verification(token);
CREATE INDEX idx_verification_email ON verification(email);
```

### **Database Query Functions**: `lib/db/queries.ts`

#### **Usage Tracking Queries**
```typescript
export async function getUserMessageCount(user: User): Promise<{ count: number } | { error: string }> {
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const result = await db
      .select({ count: sql<number>`count(*)` })
      .from(messageUsage)
      .where(and(
        eq(messageUsage.userId, user.id),
        gte(messageUsage.date, today)
      ));

    return { count: result[0]?.count || 0 };
  } catch (error) {
    console.error('Error getting user message count:', error);
    return { error: 'Failed to get message count' };
  }
}

export async function incrementMessageUsage({ userId }: { userId: string }): Promise<void> {
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    await db
      .insert(messageUsage)
      .values({
        id: generateId(),
        userId,
        date: today,
        messageCount: 1,
      })
      .onConflictDoUpdate({
        target: [messageUsage.userId, messageUsage.date],
        set: {
          messageCount: sql`${messageUsage.messageCount} + 1`,
          updatedAt: new Date(),
        },
      });
  } catch (error) {
    console.error('Error incrementing message usage:', error);
  }
}

export async function getExtremeSearchUsageCount(user: User): Promise<{ count: number }> {
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const result = await db
      .select({ count: sql<number>`count(*)` })
      .from(extremeSearchUsage)
      .where(and(
        eq(extremeSearchUsage.userId, user.id),
        gte(extremeSearchUsage.date, today)
      ));

    return { count: result[0]?.count || 0 };
  } catch (error) {
    console.error('Error getting extreme search usage:', error);
    return { count: 0 };
  }
}
```

#### **Chat Management Queries**
```typescript
export async function saveChat({ id, userId, title, visibility }: SaveChatProps) {
  try {
    await db.insert(chat).values({
      id,
      userId,
      title,
      visibility,
    });
  } catch (error) {
    console.error('Failed to save chat:', error);
    throw error;
  }
}

export async function getChatById({ id }: { id: string }) {
  try {
    const [chat] = await db.select().from(chat).where(eq(chat.id, id));
    return chat;
  } catch (error) {
    console.error('Failed to get chat by id:', error);
    throw error;
  }
}

export async function saveMessages({ messages }: { messages: MessageDBInsert[] }) {
  try {
    await db.insert(message).values(messages);
  } catch (error) {
    console.error('Failed to save messages:', error);
    throw error;
  }
}

export async function createStreamId({ streamId, chatId }: { streamId: string; chatId: string }) {
  try {
    await db.insert(stream).values({
      id: streamId,
      chatId,
    });
  } catch (error) {
    console.error('Failed to create stream ID:', error);
    throw error;
  }
}
```

### **Database Connection and Configuration**

#### **Database Configuration**
```typescript
// lib/db/index.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  throw new Error('DATABASE_URL is not set');
}

// Configure postgres client for optimal performance
const client = postgres(connectionString, {
  max: 20, // Maximum number of connections
  idle_timeout: 20, // Close idle connections after 20 seconds
  connect_timeout: 10, // Connection timeout
});

export const db = drizzle(client, {
  schema: schema,
  logger: process.env.NODE_ENV === 'development',
});

// Database health check
export async function checkDatabaseHealth() {
  try {
    await db.select().from(user).limit(1);
    return { status: 'healthy' };
  } catch (error) {
    console.error('Database health check failed:', error);
    return { status: 'unhealthy', error };
  }
}
```

---

## File Structure & Key Components

### **Complete Directory Structure**

```
scira/
├── app/
│   ├── api/
│   │   ├── search/
│   │   │   └── route.ts              # Main search API endpoint (Lines 107-670)
│   │   └── chat/
│   │       └── route.ts              # Chat API endpoint
│   ├── actions.ts                    # Server-side actions
│   ├── globals.css                   # Global styles
│   ├── layout.tsx                    # Root layout
│   └── page.tsx                      # Home page
│
├── lib/
│   ├── tools/
│   │   ├── extreme-search.ts         # Deep research system (Lines 192-758)
│   │   ├── web-search.ts            # Multi-provider search (Lines 629-718)
│   │   ├── x-search.ts              # X (Twitter) search
│   │   ├── academic-search.ts       # Academic paper search
│   │   ├── youtube-search.ts        # YouTube search
│   │   ├── reddit-search.ts         # Reddit search
│   │   ├── movie-tv-search.ts       # Movie/TV search
│   │   ├── stock-chart.ts           # Stock chart tool
│   │   ├── currency-converter.ts    # Currency conversion
│   │   ├── weather.ts               # Weather information
│   │   ├── code-interpreter.ts       # Code execution tool
│   │   ├── text-translate.ts        # Text translation
│   │   ├── flight-tracker.ts        # Flight tracking
│   │   ├── supermemory.ts           # Memory tools (Lines 1-44)
│   │   ├── connectors-search.ts     # Document connectors (Lines 1-313)
│   │   └── index.ts                 # Tool exports
│   │
│   ├── db/
│   │   ├── schema.ts                # Database schema definitions
│   │   ├── queries.ts               # Database query functions
│   │   └── index.ts                 # Database exports
│   │
│   ├── ai/
│   │   ├── providers.ts             # AI provider configurations
│   │   └── index.ts                 # AI exports
│   │
│   ├── auth-utils.ts                # Authentication utilities
│   ├── rate-limit.ts                # Rate limiting implementation
│   ├── constants.ts                 # Application constants
│   ├── connectors.tsx               # Connector configurations
│   ├── memory-actions.ts            # Memory operations (Lines 1-118)
│   ├── user-data-server.ts          # Server-side user data
│   ├── parser.ts                    # Text parsing utilities
│   ├── types.ts                     # TypeScript type definitions
│   └── errors.ts                    # Error handling classes
│
├── components/
│   ├── ui/                          # Reusable UI components
│   ├── chat/                        # Chat-related components
│   ├── search/                      # Search-related components
│   ├── memory-dialog.tsx            # Memory management UI
│   └── connectors-search-results.tsx # Document search results
│
├── public/
│   ├── icons/                       # Icon assets
│   └── supermemory.svg              # Supermemory logo
│
├── env/
│   ├── server.ts                    # Server environment variables
│   └── client.ts                    # Client environment variables
│
├── hooks/                           # Custom React hooks
├── styles/                          # Style files
├── utils/                           # Utility functions
├── middleware.ts                    # Next.js middleware
├── next.config.js                   # Next.js configuration
├── package.json                     # Dependencies
├── tsconfig.json                    # TypeScript configuration
├── tailwind.config.js               # Tailwind CSS configuration
└── README.md                        # Project documentation
```

### **Key Component Responsibilities**

| Component | File Path | Purpose | Key Features |
|-----------|-----------|---------|--------------|
| **Main Search API** | `app/api/search/route.ts` | Primary search endpoint | Authentication, rate limiting, streaming, tool orchestration |
| **Extreme Search** | `lib/tools/extreme-search.ts` | AI-driven deep research | Research planning, autonomous agent, multi-tool execution |
| **Web Search** | `lib/tools/web-search.ts` | Multi-provider search | Strategy pattern, deduplication, real-time streaming |
| **X Search** | `lib/tools/x-search.ts` | Social media search | Real-time X search, tweet content retrieval |
| **Supermemory** | `lib/tools/supermemory.ts` | Personal knowledge | User-specific memory search and storage |
| **Document Connectors** | `lib/tools/connectors-search.ts` | Document search | Google Drive, Notion, OneDrive integration |
| **Database Schema** | `lib/db/schema.ts` | Data structure | PostgreSQL tables with 27 optimized indexes |
| **Authentication Utils** | `lib/auth-utils.ts` | User authentication | Better Auth integration, session management |
| **Rate Limiting** | `lib/rate-limit.ts` | Usage control | Redis-based rate limiting with tiers |
| **Memory Actions** | `lib/memory-actions.ts` | Memory operations | CRUD operations for personal memories |
| **AI Providers** | `lib/ai/providers.ts` | Model configuration | Multiple AI model routing and configuration |

### **Core Function References**

#### **Search Functions**
- **Main Search Entry**: `app/api/search/route.ts:107` - `POST()` function
- **Extreme Search**: `lib/tools/extreme-search.ts:192` - `extremeSearch()` function
- **Web Search Tool**: `lib/tools/web-search.ts:633` - `webSearchTool()` function
- **Search Strategy Factory**: `lib/tools/web-search.ts:610` - `createSearchStrategy()`

#### **Content Processing**
- **Content Retrieval**: `lib/tools/extreme-search.ts:112` - `getContents()` function
- **Domain Deduplication**: `lib/tools/web-search.ts:26` - `deduplicateByDomainAndUrl()`
- **Title Cleaning**: `lib/tools/web-search.ts:17` - `cleanTitle()` function

#### **Authentication & Rate Limiting**
- **Lightweight User Check**: `app/api/search/route.ts:126` - `getLightweightUser()`
- **Rate Limit Check**: `app/api/search/route.ts:131` - `unauthenticatedRateLimit.limit()`
- **Usage Tracking**: `app/api/search/route.ts:589` - `incrementMessageUsage()`

#### **Database Operations**
- **Save Messages**: `lib/db/queries.ts` - `saveMessages()` function
- **Usage Queries**: `lib/db/queries.ts` - `getUserMessageCount()` function
- **Chat Management**: `lib/db/queries.ts` - `saveChat()` and `getChatById()`

#### **Streaming & Real-time**
- **Stream Creation**: `app/api/search/route.ts:287` - `createUIMessageStream()`
- **Tool Streaming**: `lib/tools/extreme-search.ts:422` - `dataStream.write()` calls
- **Progress Updates**: `lib/tools/web-search.ts:126` - `data-query_completion` events

---

## Error Handling & Fallbacks

### **Multi-Provider Fallback Strategy**

#### **Provider Strategy Implementation**
```typescript
// lib/tools/web-search.ts:610-627
const createSearchStrategy = (
  provider: 'exa' | 'parallel' | 'tavily' | 'firecrawl',
  clients: {
    exa: Exa;
    parallel: Parallel;
    firecrawl: FirecrawlApp;
    tvly: TavilyClient;
  },
): SearchStrategy => {
  const strategies = {
    parallel: () => new ParallelSearchStrategy(clients.parallel, clients.firecrawl),
    tavily: () => new TavilySearchStrategy(clients.tvly),
    firecrawl: () => new FirecrawlSearchStrategy(clients.firecrawl),
    exa: () => new ExaSearchStrategy(clients.exa),
  };

  return strategies[provider]();
};
```

#### **Content Retrieval Fallback**: `lib/tools/extreme-search.ts:112-190`
```typescript
const getContents = async (links: string[]) => {
  const results: SearchResult[] = [];
  const failedUrls: string[] = [];

  // Primary: Try Exa for all URLs
  try {
    const result = await exa.getContents(links, {
      text: { maxCharacters: 3000, includeHtmlTags: false },
      livecrawl: 'preferred',
    });

    // Process successful results
    for (const r of result.results) {
      if (r.text && r.text.trim()) {
        results.push({
          title: r.title || r.url.split('/').pop() || 'Retrieved Content',
          url: r.url,
          content: r.text,
          publishedDate: r.publishedDate || '',
          favicon: r.favicon || `https://www.google.com/s2/favicons?domain=${new URL(r.url).hostname}&sz=128`,
        });
      } else {
        failedUrls.push(r.url); // Add to fallback list
      }
    }

    // Add missing URLs to failed list
    const exaUrls = result.results.map((r) => r.url);
    const missingUrls = links.filter((url) => !exaUrls.includes(url));
    failedUrls.push(...missingUrls);
  } catch (error) {
    console.error('Exa API error:', error);
    failedUrls.push(...links); // All URLs to fallback
  }

  // Fallback: Use Firecrawl for failed URLs
  if (failedUrls.length > 0) {
    console.log(`Using Firecrawl fallback for ${failedUrls.length} URLs:`, failedUrls);

    for (const url of failedUrls) {
      try {
        const scrapeResponse = await firecrawl.scrape(url, {
          formats: ['markdown'],
          proxy: 'auto',
          storeInCache: true,
          parsers: ['pdf'],
        });

        if (scrapeResponse.markdown) {
          results.push({
            title: scrapeResponse.metadata?.title || url.split('/').pop() || 'Retrieved Content',
            url: url,
            content: scrapeResponse.markdown.slice(0, 3000),
            publishedDate: (scrapeResponse.metadata?.publishedDate as string) || '',
            favicon: `https://www.google.com/s2/favicons?domain=${new URL(url).hostname}&sz=128`,
          });
        }
      } catch (firecrawlError) {
        console.error(`Firecrawl error for ${url}:`, firecrawlError);
        // Continue with other URLs even if one fails
      }
    }
  }

  return results;
};
```

#### **Search Strategy Error Handling**
```typescript
// lib/tools/web-search.ts:199-215, 336-355, 468-487, 582-601 (similar patterns in each strategy)

// Example from ParallelSearchStrategy
try {
  const [singleResponse, firecrawlImages] = await Promise.all([
    this.parallel.beta.search(searchParams),
    this.firecrawl.search(query, { sources: ['images'], limit: 3 }),
  ]);

  return { query, results, images };
} catch (error) {
  console.error(`Parallel AI search error for query "${query}":`, error);

  // Stream error notification
  options.dataStream?.write({
    type: 'data-query_completion',
    data: {
      query,
      index,
      total: limitedQueries.length,
      status: 'error',
      resultsCount: 0,
      imagesCount: 0,
    },
  });

  return { query, results: [], images: [] }; // Graceful fallback
}
```

### **API Error Handling**

#### **SDK Error Classes**: `lib/errors.ts`
```typescript
export class ChatSDKError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode: number = 400,
  ) {
    super(message);
    this.name = 'ChatSDKError';
  }

  toResponse(): Response {
    return new Response(
      JSON.stringify({
        error: {
          code: this.code,
          message: this.message,
        },
      }),
      {
        status: this.statusCode,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

// Usage examples
export const errors = {
  unauthorized: (message: string) => new ChatSDKError('unauthorized', message, 401),
  rateLimit: (message: string) => new ChatSDKError('rate_limit', message, 429),
  forbidden: (message: string) => new ChatSDKError('forbidden', message, 403),
  notFound: (message: string) => new ChatSDKError('not_found', message, 404),
  badRequest: (message: string) => new ChatSDKError('bad_request', message, 400),
  upgradeRequired: (message: string) => new ChatSDKError('upgrade_required', message, 402),
  internalError: (message: string) => new ChatSDKError('internal_error', message, 500),
};
```

#### **Search API Error Handling**: `app/api/search/route.ts:133-140, 234-254, 636-641`
```typescript
// Rate limit error handling
if (!success) {
  const resetDate = new Date(reset);
  return new ChatSDKError(
    'rate_limit:api',
    `You've reached the limit of ${limit} searches per day for unauthenticated users. Sign in for more searches or wait until ${resetDate.toLocaleString()}.`
  ).toResponse();
}

// Authentication error handling
if (requiresAuthentication(model)) {
  return new ChatSDKError('unauthorized:model', `${model} requires authentication`).toResponse();
}

// Stream error handling
onError(error) {
  console.log('Error: ', error);
  if (error instanceof Error && error.message.includes('Rate Limit')) {
    return 'Oops, you have reached the rate limit! Please try again later.';
  }
  return 'Oops, an error occurred!';
}
```

### **Graceful Degradation Patterns**

#### **Retry Logic with Exponential Backoff**
```typescript
// Utility function for retrying failed operations
const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000,
): Promise<T> => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;

      const delay = baseDelay * Math.pow(2, i);
      console.log(`Retrying after ${delay}ms (attempt ${i + 2}/${maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  throw new Error('Max retries exceeded');
};

// Usage in content retrieval
const contents = await retryWithBackoff(
  () => exa.getContents(links, options),
  3, // max 3 retries
  1000 // 1 second base delay
);
```

#### **Circuit Breaker Pattern**
```typescript
// Circuit breaker for API calls to prevent cascading failures
class CircuitBreaker {
  private failures = 0;
  private lastFailureTime = 0;
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  private readonly threshold = 5; // Failures before opening
  private readonly timeout = 60000; // 1 minute timeout

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = 'CLOSED';
  }

  private onFailure() {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.failures >= this.threshold) {
      this.state = 'OPEN';
    }
  }
}

// Usage with search providers
const searchCircuitBreaker = new CircuitBreaker();
const results = await searchCircuitBreaker.execute(() => exa.searchAndContents(query));
```

#### **Partial Result Handling**
```typescript
// Handle partial failures in multi-provider searches
const searchPromises = providers.map(async (provider) => {
  try {
    return await searchWithProvider(provider, query);
  } catch (error) {
    console.error(`Provider ${provider} failed:`, error);
    return { provider, results: [], error: error.message };
  }
});

const searchResults = await Promise.allSettled(searchPromises);

// Process mixed successful and failed results
const validResults = searchResults
  .filter((result): result is PromiseFulfilledResult<any> => result.status === 'fulfilled')
  .map(result => result.value.results)
  .flat();

const failedProviders = searchResults
  .filter((result): result is PromiseRejectedResult => result.status === 'rejected')
  .map(result => result.reason);

if (validResults.length === 0 && failedProviders.length > 0) {
  throw new Error(`All search providers failed: ${failedProviders.join(', ')}`);
}
```

### **Error Recovery and Monitoring**

#### **Error Logging and Monitoring**
```typescript
// Structured error logging
export const logError = (error: Error, context: Record<string, any>) => {
  const errorData = {
    message: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString(),
    context,
    // Add user ID if available
    userId: context.userId || 'anonymous',
    // Add request ID for tracing
    requestId: context.requestId || generateRequestId(),
  };

  console.error(JSON.stringify(errorData));

  // Send to monitoring service (e.g., Sentry, LogRocket)
  if (process.env.NODE_ENV === 'production') {
    // sendToMonitoring(errorData);
  }
};

// Usage in search API
try {
  const results = await performSearch(query);
  return results;
} catch (error) {
  logError(error as Error, {
    operation: 'search',
    query,
    userId: user?.id,
    provider: searchProvider,
  });
  throw error;
}
```

#### **Health Check Implementation**
```typescript
// Health check for external services
export const checkServiceHealth = async () => {
  const services = {
    database: await checkDatabaseHealth(),
    redis: await checkRedisHealth(),
    exa: await checkApiHealth('https://api.exa.ai'),
    parallel: await checkApiHealth('https://api.parallel.ai'),
    firecrawl: await checkApiHealth('https://api.firecrawl.dev'),
  };

  const healthyServices = Object.entries(services)
    .filter(([_, health]) => health.status === 'healthy')
    .map(([name]) => name);

  const unhealthyServices = Object.entries(services)
    .filter(([_, health]) => health.status !== 'healthy')
    .map(([name, health]) => ({ name, error: health.error }));

  return {
    status: unhealthyServices.length === 0 ? 'healthy' : 'degraded',
    services,
    healthyServices,
    unhealthyServices,
  };
};

// API endpoint for health checks
export async function GET() {
  const health = await checkServiceHealth();

  return Response.json(health, {
    status: health.status === 'healthy' ? 200 : 503,
  });
}
```

---

## Security & Privacy

### **Authentication System**

#### **Better Auth Integration**
```typescript
// lib/auth-utils.ts
import { auth } from '@/lib/auth';

export async function getCurrentUser() {
  const session = await auth();
  return session?.user;
}

export async function getLightweightUser() {
  const session = await auth();
  if (!session?.user) return null;

  return {
    userId: session.user.id,
    email: session.user.email,
    isProUser: session.user.isProUser || false,
  };
}

export async function requireAuth() {
  const user = await getCurrentUser();
  if (!user) {
    throw new ChatSDKError('unauthorized', 'Authentication required', 401);
  }
  return user;
}
```

#### **Middleware Authentication**
```typescript
// middleware.ts
import { auth } from '@/lib/auth';

export default auth((req) => {
  // Add user information to request headers for API routes
  if (req.auth?.user) {
    const requestHeaders = new Headers(req.headers);
    requestHeaders.set('x-user-id', req.auth.user.id);
    requestHeaders.set('x-user-email', req.auth.user.email || '');

    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    });
  }

  return NextResponse.next();
});

export const config = {
  matcher: ['/api/:path*', '/chat/:path*'],
};
```

### **Data Isolation and Privacy**

#### **User Data Isolation**
```typescript
// Memory isolation with container tags
export function createMemoryTools(userId: string) {
  return supermemoryTools(serverEnv.SUPERMEMORY_API_KEY, {
    containerTags: [userId], // Ensures data isolation per user
  });
}

// Document search isolation
export function createConnectorsSearchTool(userId: string, selectedConnectors?: ConnectorProvider[]) {
  return tool({
    execute: async ({ query, provider = 'all' }) => {
      const result = await client.search.documents({
        q: query,
        containerTags: [userId, config.syncTag], // User + provider isolation
        limit: 15,
        rerank: true,
      });

      return result;
    },
  });
}
```

#### **Database Row Level Security**
```typescript
// All queries include user filtering
export async function getUserChats(userId: string) {
  return await db
    .select()
    .from(chat)
    .where(eq(chat.userId, userId)); // Automatic user filtering
}

export async function getChatByIdWithAuth({ id, userId }: { id: string; userId: string }) {
  const [chat] = await db
    .select()
    .from(chat)
    .where(and(
      eq(chat.id, id),
      eq(chat.userId, userId) // User ownership verification
    ));

  return chat;
}
```

### **API Security**

#### **API Key Management**
```typescript
// env/server.ts - Server-side environment variables
export const serverEnv = createEnv({
  server: {
    // Search API Keys
    EXA_API_KEY: z.string().min(1),
    PARALLEL_API_KEY: z.string().min(1),
    FIRECRAWL_API_KEY: z.string().min(1),
    TAVILY_API_KEY: z.string().min(1),
    DAYTONA_API_KEY: z.string().min(1),

    // Memory and Integration Keys
    SUPERMEMORY_API_KEY: z.string().min(1),

    // Database and Caching
    DATABASE_URL: z.string().url(),
    UPSTASH_REDIS_REST_URL: z.string().url(),
    UPSTASH_REDIS_REST_TOKEN: z.string().min(1),

    // Authentication
    AUTH_SECRET: z.string().min(1),
    GITHUB_CLIENT_ID: z.string().min(1),
    GITHUB_CLIENT_SECRET: z.string().min(1),
    GOOGLE_CLIENT_ID: z.string().min(1),
    GOOGLE_CLIENT_SECRET: z.string().min(1),
  },
  runtimeEnv: process.env,
});

// Secure client initialization
const initializeSecureClients = () => {
  return {
    exa: new Exa(serverEnv.EXA_API_KEY),
    parallel: new Parallel({ apiKey: serverEnv.PARALLEL_API_KEY }),
    firecrawl: new FirecrawlApp({ apiKey: serverEnv.FIRECRAWL_API_KEY }),
    tvly: tavily({ apiKey: serverEnv.TAVILY_API_KEY }),
    daytona: new Daytona({ apiKey: serverEnv.DAYTONA_API_KEY }),
    supermemory: new Supermemory({ apiKey: serverEnv.SUPERMEMORY_API_KEY }),
  };
};
```

#### **Request Validation and Sanitization**
```typescript
// Input validation schemas
export const searchRequestSchema = z.object({
  messages: z.array(messageSchema).min(1),
  model: z.string().min(1),
  group: z.enum(['default', 'extreme']).default('default'),
  searchProvider: z.enum(['exa', 'parallel', 'tavily', 'firecrawl']).default('parallel'),
  selectedConnectors: z.array(z.string()).optional(),
});

// Query parameter sanitization
export const sanitizeQuery = (query: string): string => {
  return query
    .trim()
    .slice(0, 1000) // Limit query length
    .replace(/[<>]/g, '') // Remove potential HTML
    .replace(/javascript:/gi, '') // Remove JavaScript protocol
    .replace(/data:/gi, ''); // Remove data protocol
};

// URL validation
export const isValidUrl = (url: string): boolean => {
  try {
    const urlObj = new URL(url);
    return ['http:', 'https:'].includes(urlObj.protocol);
  } catch {
    return false;
  }
};
```

### **Content Security**

#### **Content Sanitization**
```typescript
// HTML content sanitization
import { JSDOM } from 'jsdom';

export const sanitizeHtmlContent = (html: string): string => {
  const dom = new JSDOM(html);
  const document = dom.window.document;

  // Remove script tags and dangerous attributes
  const scripts = document.querySelectorAll('script');
  scripts.forEach(script => script.remove());

  const dangerousElements = document.querySelectorAll('[onclick], [onload], [onerror]');
  dangerousElements.forEach(el => {
    el.removeAttribute('onclick');
    el.removeAttribute('onload');
    el.removeAttribute('onerror');
  });

  return document.body.innerHTML || '';
};

// Text content cleaning
export const sanitizeTextContent = (text: string): string => {
  return text
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim()
    .slice(0, 10000); // Reasonable length limit
};
```

#### **CORS and Security Headers**
```typescript
// next.config.js
const nextConfig = {
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },
};

// CORS configuration for API routes
export const corsHeaders = {
  'Access-Control-Allow-Origin': process.env.NODE_ENV === 'production'
    ? 'https://scira.ai'
    : 'http://localhost:3000',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-User-ID',
  'Access-Control-Max-Age': '86400',
};
```

### **Privacy Protection**

#### **Data Minimization**
```typescript
// Only collect necessary user data
export const createLightweightUser = (user: User) => ({
  userId: user.id,
  email: user.email,
  isProUser: user.subscriptions?.some(s => s.status === 'active') || false,
  // Exclude sensitive information like password hashes, personal data, etc.
});

// Anonymized analytics
export const trackUsage = async (userId: string, action: string, metadata?: any) => {
  const analyticsData = {
    userId: hashUserId(userId), // Hash user ID for privacy
    action,
    timestamp: new Date().toISOString(),
    metadata: sanitizeMetadata(metadata), // Remove PII
  };

  // Send to analytics service
  await sendAnalytics(analyticsData);
};

const hashUserId = (userId: string): string => {
  return crypto.createHash('sha256').update(userId + process.env.HASH_SALT).digest('hex');
};
```

#### **Data Retention Policies**
```typescript
// Automated data cleanup
export const cleanupOldData = async () => {
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  // Delete old usage data
  await db
    .delete(messageUsage)
    .where(lt(messageUsage.date, thirtyDaysAgo));

  await db
    .delete(extremeSearchUsage)
    .where(lt(extremeSearchUsage.date, thirtyDaysAgo));

  // Delete old chat history for non-pro users (configurable retention period)
  const retentionDays = 90; // 3 months for free users
  const retentionDate = new Date();
  retentionDate.setDate(retentionDate.getDate() - retentionDays);

  await db
    .delete(message)
    .where(and(
      lt(message.createdAt, retentionDate),
      inArray(
        message.userId,
        db.select({ userId: user.id }).from(user).where(notExists(
          db.select().from(subscription).where(eq(subscription.userId, user.id))
        ))
      )
    ));
};
```

---

## Environment Configuration

### **Server Environment**: `env/server.ts`

```typescript
import { createEnv } from '@t3-oss/env-nextjs';
import { z } from 'zod';

export const serverEnv = createEnv({
  server: {
    // Database Configuration
    DATABASE_URL: z.string().url(),

    // Redis/Upstash Configuration
    UPSTASH_REDIS_REST_URL: z.string().url(),
    UPSTASH_REDIS_REST_TOKEN: z.string().min(1),

    // Authentication
    AUTH_SECRET: z.string().min(32),
    AUTH_URL: z.string().url().optional(),

    // OAuth Providers
    GITHUB_CLIENT_ID: z.string().min(1),
    GITHUB_CLIENT_SECRET: z.string().min(1),
    GOOGLE_CLIENT_ID: z.string().min(1),
    GOOGLE_CLIENT_SECRET: z.string().min(1),

    // Search API Providers
    EXA_API_KEY: z.string().min(1),
    PARALLEL_API_KEY: z.string().min(1),
    FIRECRAWL_API_KEY: z.string().min(1),
    TAVILY_API_KEY: z.string().min(1),

    // AI Model Providers
    OPENAI_API_KEY: z.string().min(1),
    ANTHROPIC_API_KEY: z.string().min(1),
    XAI_API_KEY: z.string().min(1),
    GROQ_API_KEY: z.string().min(1),
    GOOGLE_AI_API_KEY: z.string().min(1),
    COHERE_API_KEY: z.string().min(1),

    // Code Execution
    DAYTONA_API_KEY: z.string().min(1),

    // Memory and Knowledge
    SUPERMEMORY_API_KEY: z.string().min(1),

    // Payment and Subscriptions
    POLAR_ACCESS_TOKEN: z.string().min(1),
    POLAR_WEBHOOK_SECRET: z.string().min(1),

    // Email and Notifications
    RESEND_API_KEY: z.string().min(1),
    RESEND_FROM_EMAIL: z.string().email(),

    // Monitoring and Analytics
    VERCEL_ANALYTICS_ID: z.string().optional(),
    SENTRY_DSN: z.string().optional(),
    SENTRY_AUTH_TOKEN: z.string().optional(),

    // Application Settings
    NODE_ENV: z.enum(['development', 'production', 'test']),
    LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  },
  runtimeEnv: process.env,
  emptyStringAsUndefined: true,
});
```

### **Client Environment**: `env/client.ts`

```typescript
import { createEnv } from '@t3-oss/env-nextjs';
import { z } from 'zod';

export const clientEnv = createEnv({
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
    NEXT_PUBLIC_POLAR_CHECKOUT_URL: z.string().url(),
    NEXT_PUBLIC_POLAR_SUCCESS_URL: z.string().url(),
    NEXT_PUBLIC_SUPERMEMORY_URL: z.string().url().optional(),
  },
  runtimeEnv: process.env,
  emptyStringAsUndefined: true,
});
```

### **Configuration Management**

#### **AI Provider Configuration**: `lib/ai/providers.ts`
```typescript
import { createOpenAI } from '@ai-sdk/openai';
import { createAnthropic } from '@ai-sdk/anthropic';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { xai } from '@ai-sdk/xai';
import { groq } from '@ai-sdk/groq';
import { cohere } from '@ai-sdk/cohere';

export const scira = {
  languageModel: (model: string) => {
    // OpenAI Models
    if (model.startsWith('gpt-')) {
      return createOpenAI({
        apiKey: serverEnv.OPENAI_API_KEY,
        compatibility: 'compatible',
      })(model);
    }

    // Anthropic Models
    if (model.startsWith('claude-')) {
      return createAnthropic({
        apiKey: serverEnv.ANTHROPIC_API_KEY,
      })(model);
    }

    // XAI Models
    if (model.includes('grok-')) {
      return xai(model);
    }

    // Google Models
    if (model.includes('gemini-')) {
      return createGoogleGenerativeAI({
        apiKey: serverEnv.GOOGLE_AI_API_KEY,
      })(model);
    }

    // Groq Models
    if (model.startsWith('llama-') || model.startsWith('mixtral-')) {
      return groq(model);
    }

    // Cohere Models
    if (model.startsWith('command-')) {
      return cohere(model);
    }

    throw new Error(`Unsupported model: ${model}`);
  },

  // Model-specific configurations
  modelParameters: (model: string) => {
    const baseParams = {
      temperature: 0.7,
      maxTokens: 4000,
    };

    // Adjust parameters based on model capabilities
    if (model.includes('reasoning') || model.includes('think')) {
      return {
        ...baseParams,
        temperature: 0.1, // Lower temperature for reasoning models
        maxTokens: 8000,   // Higher token limit for complex reasoning
      };
    }

    if (model.includes('fast') || model.includes('quick')) {
      return {
        ...baseParams,
        temperature: 0.5,
        maxTokens: 2000,   // Lower token limit for faster responses
      };
    }

    return baseParams;
  },
};
```

#### **Search Provider Configuration**
```typescript
// lib/tools/web-search.ts:684-690
export function webSearchTool(
  dataStream?: UIMessageStreamWriter<ChatMessage>,
  searchProvider: 'exa' | 'parallel' | 'tavily' | 'firecrawl' = 'parallel',
) {
  return tool({
    description: 'Multi-provider web search tool',
    inputSchema: z.object({
      queries: z.array(z.string()).min(3),
      maxResults: z.array(z.number()).min(1).optional(),
      topics: z.array(z.enum(['general', 'news'])).optional(),
      quality: z.array(z.enum(['default', 'best'])).optional(),
    }),
    execute: async ({ queries, maxResults, topics, quality }) => {
      // Initialize all clients with environment variables
      const clients = {
        exa: new Exa(serverEnv.EXA_API_KEY),
        parallel: new Parallel({ apiKey: serverEnv.PARALLEL_API_KEY }),
        firecrawl: new FirecrawlApp({ apiKey: serverEnv.FIRECRAWL_API_KEY }),
        tvly: tavily({ apiKey: serverEnv.TAVILY_API_KEY }),
      };

      // Create strategy based on provider selection
      const strategy = createSearchStrategy(searchProvider, clients);

      // Execute search with fallback parameters
      return await strategy.search(queries, {
        maxResults: maxResults || new Array(queries.length).fill(10),
        topics: topics || new Array(queries.length).fill('general'),
        quality: quality || new Array(queries.length).fill('default'),
        dataStream,
      });
    },
  });
}
```

---

## Deployment & Operations

### **Production Deployment Configuration**

#### **Vercel Configuration**: `vercel.json`
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "env": {
    "NODE_ENV": "production"
  },
  "functions": {
    "app/api/search/route.ts": {
      "maxDuration": 30,
      "memory": 1024
    },
    "app/api/chat/route.ts": {
      "maxDuration": 60,
      "memory": 2048
    }
  },
  "regions": ["iad1", "sfo1"],
  "framework": "nextjs"
}
```

#### **Docker Configuration**: `Dockerfile`
```dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN \
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
  elif [ -f package-lock.json ]; then npm ci; \
  elif [ -f pnpm-lock.yaml ]; then yarn global add pnpm && pnpm i --frozen-lockfile; \
  else echo "Lockfile not found." && exit 1; \
  fi

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

### **Monitoring and Observability**

#### **Health Check Endpoint**: `app/api/health/route.ts`
```typescript
import { NextResponse } from 'next/server';
import { checkDatabaseHealth, checkRedisHealth } from '@/lib/health';

export async function GET() {
  const startTime = Date.now();

  try {
    const [dbHealth, redisHealth] = await Promise.all([
      checkDatabaseHealth(),
      checkRedisHealth(),
    ]);

    const responseTime = Date.now() - startTime;
    const isHealthy = dbHealth.status === 'healthy' && redisHealth.status === 'healthy';

    return NextResponse.json({
      status: isHealthy ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      responseTime: `${responseTime}ms`,
      services: {
        database: dbHealth,
        redis: redisHealth,
      },
      version: process.env.npm_package_version || 'unknown',
    }, {
      status: isHealthy ? 200 : 503,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    });
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
    }, {
      status: 500,
    });
  }
}
```

#### **Error Tracking with Sentry**
```typescript
// lib/monitoring/sentry.ts
import * as Sentry from '@sentry/nextjs';

export const initSentry = () => {
  if (process.env.NODE_ENV === 'production' && process.env.SENTRY_DSN) {
    Sentry.init({
      dsn: process.env.SENTRY_DSN,
      tracesSampleRate: 0.1,
      environment: process.env.NODE_ENV,
      beforeSend(event) {
        // Filter out sensitive information
        if (event.request?.cookies) {
          delete event.request.cookies;
        }
        return event;
      },
    });
  }
};

// Custom error reporting
export const reportError = (error: Error, context: Record<string, any>) => {
  if (process.env.NODE_ENV === 'production') {
    Sentry.captureException(error, {
      tags: context,
      user: context.userId ? { id: context.userId } : undefined,
    });
  }
};

// Performance monitoring
export const reportPerformance = (name: string, value: number, unit: string = 'ms') => {
  if (process.env.NODE_ENV === 'production') {
    Sentry.metrics.timing(name, value, unit);
  }
};
```

### **Database Operations and Maintenance**

#### **Database Migration Script**
```typescript
// scripts/migrate.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import { migrate } from 'drizzle-orm/postgres-js/migrator';
import postgres from 'postgres';
import { serverEnv } from '@/env/server';

const migrationClient = postgres(serverEnv.DATABASE_URL, { max: 1 });
const db = drizzle(migrationClient);

async function runMigrations() {
  try {
    console.log('Running database migrations...');
    await migrate(db, { migrationsFolder: './drizzle' });
    console.log('Migrations completed successfully');
  } catch (error) {
    console.error('Migration failed:', error);
    process.exit(1);
  } finally {
    await migrationClient.end();
  }
}

runMigrations();
```

#### **Database Backup Strategy**
```bash
#!/bin/bash
# scripts/backup-db.sh

# Configuration
DB_URL="$DATABASE_URL"
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/scira_backup_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Perform database backup
pg_dump "$DB_URL" > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Remove backups older than 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### **Performance Optimization**

#### **Caching Strategy Implementation**
```typescript
// lib/cache/redis-cache.ts
import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: serverEnv.UPSTASH_REDIS_REST_URL,
  token: serverEnv.UPSTASH_REDIS_REST_TOKEN,
});

export class CacheService {
  private readonly defaultTTL = 600; // 10 minutes

  async get<T>(key: string): Promise<T | null> {
    try {
      const value = await redis.get(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      console.error('Cache get error:', error);
      return null;
    }
  }

  async set(key: string, value: any, ttl: number = this.defaultTTL): Promise<void> {
    try {
      await redis.set(key, JSON.stringify(value), { ex: ttl });
    } catch (error) {
      console.error('Cache set error:', error);
    }
  }

  async invalidate(pattern: string): Promise<void> {
    try {
      const keys = await redis.keys(pattern);
      if (keys.length > 0) {
        await redis.del(...keys);
      }
    } catch (error) {
      console.error('Cache invalidation error:', error);
    }
  }

  // Cache key generators
  static keys = {
    userSearchCache: (userId: string, query: string) => `search:user:${userId}:${Buffer.from(query).toString('base64')}`,
    rateLimit: (identifier: string, window: string) => `rate_limit:${identifier}:${window}`,
    apiResponse: (endpoint: string, params: string) => `api:${endpoint}:${Buffer.from(params).toString('base64')}`,
  };
}
```

#### **API Rate Limiting Implementation**
```typescript
// lib/rate-limit/advanced-rate-limit.ts
export class AdvancedRateLimit {
  constructor(
    private redis: Redis,
    private options: {
      windowMs: number;
      maxRequests: number;
      keyGenerator: (req: Request) => string;
      skipSuccessfulRequests?: boolean;
      skipFailedRequests?: boolean;
    }
  ) {}

  async limit(req: Request): Promise<{ success: boolean; limit: number; remaining: number; reset: number }> {
    const key = this.options.keyGenerator(req);
    const now = Date.now();
    const windowStart = now - this.options.windowMs;

    try {
      // Remove expired entries
      await redis.zremrangebyscore(key, 0, windowStart);

      // Get current request count
      const count = await redis.zcard(key);

      if (count >= this.options.maxRequests) {
        const oldestRequest = await redis.zrange(key, 0, 0, { withScores: true });
        const resetTime = oldestRequest[0]?.[1] + this.options.windowMs || now + this.options.windowMs;

        return {
          success: false,
          limit: this.options.maxRequests,
          remaining: 0,
          reset: Math.ceil(resetTime / 1000),
        };
      }

      // Add current request
      await redis.zadd(key, { score: now, member: `${now}-${Math.random()}` });
      await redis.expire(key, Math.ceil(this.options.windowMs / 1000));

      return {
        success: true,
        limit: this.options.maxRequests,
        remaining: this.options.maxRequests - count - 1,
        reset: Math.ceil((now + this.options.windowMs) / 1000),
      };
    } catch (error) {
      console.error('Rate limiting error:', error);
      // Fail open - allow request if rate limiting fails
      return {
        success: true,
        limit: this.options.maxRequests,
        remaining: this.options.maxRequests,
        reset: Math.ceil((now + this.options.windowMs) / 1000),
      };
    }
  }
}
```

---

## Complete Function Reference

### **Core API Functions**

#### **Search API Endpoint**
- **File**: `app/api/search/route.ts`
- **Function**: `POST(req: Request)` - Lines 107-670
- **Purpose**: Main entry point for all search requests
- **Parameters**: Request body with messages, model, group, searchProvider
- **Returns**: Streaming response with search results

#### **Extreme Search Function**
- **File**: `lib/tools/extreme-search.ts`
- **Function**: `extremeSearch(prompt, dataStream)` - Lines 192-731
- **Purpose**: AI-driven deep research with autonomous agent
- **Parameters**: Research prompt and optional data stream
- **Returns**: Comprehensive research results with sources and analysis

#### **Web Search Tool**
- **File**: `lib/tools/web-search.ts`
- **Function**: `webSearchTool(dataStream, searchProvider)` - Lines 633-717
- **Purpose**: Multi-provider web search with strategy pattern
- **Parameters**: Data stream and search provider selection
- **Returns**: Search results with deduplication and real-time streaming

### **Database Functions**

#### **User Management**
- **File**: `lib/db/queries.ts`
- **Function**: `getCurrentUser()` - Get authenticated user details
- **Function**: `getLightweightUser()` - Get minimal user info for fast checks
- **Function**: `saveChat(chatData)` - Create or update chat session
- **Function**: `getChatById({id})` - Retrieve specific chat with authorization

#### **Usage Tracking**
- **Function**: `getUserMessageCount(user)` - Get daily message usage
- **Function**: `incrementMessageUsage({userId})` - Track message usage
- **Function**: `getExtremeSearchUsageCount(user)` - Get extreme search usage
- **Function**: `incrementExtremeSearchUsage({userId})` - Track extreme search usage

#### **Message Management**
- **Function**: `saveMessages({messages})` - Store chat messages
- **Function**: `createStreamId({streamId, chatId})` - Create stream tracking
- **Function**: `generateTitleFromUserMessage({message})` - Generate chat title

### **Tool Functions**

#### **Search Strategy Factory**
- **File**: `lib/tools/web-search.ts`
- **Function**: `createSearchStrategy(provider, clients)` - Lines 610-627
- **Purpose**: Factory for creating provider-specific search strategies
- **Returns**: SearchStrategy interface implementation

#### **Content Processing**
- **File**: `lib/tools/extreme-search.ts`
- **Function**: `searchWeb(query, category, includeDomains)` - Lines 77-110
- **Function**: `getContents(links)` - Lines 112-190
- **File**: `lib/tools/web-search.ts`
- **Function**: `deduplicateByDomainAndUrl(items)` - Lines 26-42
- **Function**: `cleanTitle(title)` - Lines 17-24

#### **Memory and Integration Tools**
- **File**: `lib/tools/supermemory.ts`
- **Function**: `createMemoryTools(userId)` - Lines 5-9
- **File**: `lib/tools/connectors-search.ts`
- **Function**: `createConnectorsSearchTool(userId, selectedConnectors)` - Lines 75-313

### **Authentication Functions**

#### **User Authentication**
- **File**: `lib/auth-utils.ts`
- **Function**: `getCurrentUser()` - Get full user session
- **Function**: `getLightweightUser()` - Get minimal user data
- **Function**: `requireAuth()` - Enforce authentication
- **Function**: `requireProSubscription()` - Enforce Pro subscription

#### **Rate Limiting**
- **File**: `lib/rate-limit.ts`
- **Function**: `getClientIdentifier(req)` - Generate client fingerprint
- **Function**: `unauthenticatedRateLimit.limit(identifier)` - Check unauthenticated limits
- **Function**: `authenticatedRateLimit.limit(identifier)` - Check authenticated limits

### **Configuration Constants**

#### **Environment Variables**
- **File**: `env/server.ts` - All server-side environment variables
- **File**: `env/client.ts` - Client-side environment variables
- **Access**: `serverEnv.VARIABLE_NAME` throughout the application

#### **Application Constants**
- **File**: `lib/constants.ts`
- **SNAPSHOT_NAME** - Daytona code execution environment
- **RATE_LIMITS** - Rate limiting thresholds
- **MODEL_CONFIGURATIONS** - AI model-specific settings

---

This comprehensive documentation provides complete coverage of the Scira AI Search Platform's architecture, implementation, and operational details. Use this as the definitive reference for understanding, maintaining, and extending the system.