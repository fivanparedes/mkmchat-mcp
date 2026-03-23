<?php

namespace App\Services;

use Illuminate\Http\Client\PendingRequest;
use Illuminate\Http\Client\RequestException;
use Illuminate\Support\Facades\Http;
use RuntimeException;

class MkmApiService
{
    private string $baseUrl;
    private ?string $apiKey;
    private string $apiKeyHeader;

    public function __construct()
    {
        $this->baseUrl = rtrim(config('mkm.api_url', 'http://localhost:8080'), '/');
        $apiKey = config('mkm.api_key');
        $this->apiKey = is_string($apiKey) && trim($apiKey) !== '' ? trim($apiKey) : null;
        $header = config('mkm.api_key_header', 'X-API-Key');
        $this->apiKeyHeader = is_string($header) && trim($header) !== '' ? trim($header) : 'X-API-Key';
    }

    /**
     * Call the Python /suggest-team endpoint.
     *
     * @param  string        $strategy         The user's strategy text.
     * @param  array<string> $ownedCharacters  Optional list of owned character names.
     * @return array  The decoded response body (keys: char1, char2, char3, strategy).
     *
     * @throws RuntimeException  On connection failure or error response from the API.
     */
    public function suggestTeam(string $strategy, array $ownedCharacters = [], ?string $model = null): array
    {
        $payload = ['strategy' => $strategy];

        if (!empty($ownedCharacters)) {
            $payload['owned_characters'] = array_values(array_filter(
                array_map('trim', $ownedCharacters)
            ));
        }

        if ($model) {
            $payload['model'] = $model;
        }

        try {
            // LLM inference can be slow — suspend the execution time limit for this call.
            set_time_limit(0);

            $response = $this->httpRequest()->timeout($this->httpTimeoutSeconds())
                ->post("{$this->baseUrl}/suggest-team", $payload);
        } catch (RequestException $e) {
            throw new RuntimeException(
                $this->pythonApiConnectionMessage($e),
                0,
                $e
            );
        }

        $body = $response->json();

        // Handle explicit error responses from the Python server.
        if ($response->failed() || isset($body['error'])) {
            $message = $body['error'] ?? "API returned HTTP {$response->status()}";
            if (isset($body['raw_response'])) {
                $message .= ' (raw LLM output could not be parsed as JSON)';
            }
            throw new RuntimeException($message);
        }

        if (!isset($body['response'])) {
            throw new RuntimeException('Unexpected API response shape: missing "response" key.');
        }

        $team = $this->normalizeTeamResponse($body['response']);

        if (!$this->hasVisibleTeamContent($team)) {
            throw new RuntimeException('API returned success but no team content was provided.');
        }

        return $team;
    }

    public function askQuestion(string $question, ?string $model = null): string
    {
        $payload = ['question' => $question];

        if ($model) {
            $payload['model'] = $model;
        }

        try {
            set_time_limit(0);

            $response = $this->httpRequest()->timeout($this->httpTimeoutSeconds())
                ->post("{$this->baseUrl}/ask-question", $payload);
        } catch (RequestException $e) {
            throw new RuntimeException(
                $this->pythonApiConnectionMessage($e),
                0,
                $e
            );
        }

        $body = $response->json();

        if ($response->failed() || isset($body['error'])) {
            throw new RuntimeException($body['error'] ?? "API returned HTTP {$response->status()}");
        }

        if (!isset($body['response'])) {
            throw new RuntimeException('Unexpected API response shape: missing "response" key.');
        }

        $text = $this->normalizeTextResponse($body['response']);

        if ($text === '') {
            throw new RuntimeException('API returned success but no answer text was provided.');
        }

        return $text;
    }

    /**
     * Explain a game mechanic (definition + recommendations from RAG + local LLM).
     *
     * @return array{definition: string, recommendations: string}
     *
     * @throws RuntimeException
     */
    public function explainMechanic(string $mechanic, ?string $model = null): array
    {
        $payload = ['mechanic' => $mechanic];

        if ($model) {
            $payload['model'] = $model;
        }

        try {
            set_time_limit(0);

            $response = $this->httpRequest()->timeout($this->httpTimeoutSeconds())
                ->post("{$this->baseUrl}/explain-mechanic", $payload);
        } catch (RequestException $e) {
            throw new RuntimeException(
                $this->pythonApiConnectionMessage($e),
                0,
                $e
            );
        }

        $body = $response->json();

        if ($response->failed() || isset($body['error'])) {
            $message = $body['error'] ?? "API returned HTTP {$response->status()}";
            if (isset($body['raw_response'])) {
                $message .= ' (raw LLM output could not be parsed as JSON)';
            }
            throw new RuntimeException($message);
        }

        if (!isset($body['response']) || !is_array($body['response'])) {
            throw new RuntimeException('Unexpected API response shape: missing "response" object.');
        }

        $inner = $body['response'];
        $definition = isset($inner['definition']) && is_string($inner['definition'])
            ? trim($inner['definition'])
            : '';
        $recommendations = isset($inner['recommendations']) && is_string($inner['recommendations'])
            ? trim($inner['recommendations'])
            : '';

        if ($definition === '' && $recommendations === '') {
            throw new RuntimeException('API returned success but no mechanic content was provided.');
        }

        return [
            'definition' => $definition,
            'recommendations' => $recommendations,
        ];
    }

    /**
     * Send one chat turn and receive the assistant response.
     *
     * @param  array<int, array{role: string, content: string}>  $messages
     * @return array{text: string, summary_text: ?string, summary_message_count: int}
     *
     * @throws RuntimeException
     */
    public function chat(
        string $message,
        array $messages,
        ?string $conversationSummary,
        int $summaryMessageCount,
        ?string $model = null,
    ): array {
        $payload = [
            'message' => $message,
            'messages' => $messages,
            'summary_text' => $conversationSummary,
            'summary_message_count' => max(0, $summaryMessageCount),
        ];

        if ($model) {
            $payload['model'] = $model;
        }

        try {
            set_time_limit(0);

            $response = $this->httpRequest()->timeout($this->httpTimeoutSeconds())
                ->post("{$this->baseUrl}/chat", $payload);
        } catch (RequestException $e) {
            throw new RuntimeException(
                $this->pythonApiConnectionMessage($e),
                0,
                $e
            );
        }

        $body = $response->json();

        if ($response->failed() || isset($body['error'])) {
            throw new RuntimeException($body['error'] ?? "API returned HTTP {$response->status()}");
        }

        if (!isset($body['response']) || !is_array($body['response'])) {
            throw new RuntimeException('Unexpected API response shape: missing "response" object.');
        }

        $inner = $body['response'];
        $text = isset($inner['text']) && is_string($inner['text'])
            ? trim($inner['text'])
            : '';

        if ($text === '') {
            throw new RuntimeException('API returned success but no chat response text was provided.');
        }

        $summaryText = isset($inner['summary_text']) && is_string($inner['summary_text'])
            ? trim($inner['summary_text'])
            : null;

        $newSummaryCount = isset($inner['summary_message_count'])
            ? max(0, (int) $inner['summary_message_count'])
            : max(0, $summaryMessageCount);

        return [
            'text' => $text,
            'summary_text' => $summaryText,
            'summary_message_count' => $newSummaryCount,
        ];
    }

    /**
     * @param  mixed  $response
     * @return array<string, mixed>
     */
    private function normalizeTeamResponse(mixed $response): array
    {
        if (is_array($response)) {
            if (isset($response['response']) && is_array($response['response'])) {
                $response = $response['response'];
            }

            if (isset($response['text']) && !isset($response['strategy'])) {
                $response['strategy'] = (string) $response['text'];
            }

            foreach (['team', 'characters'] as $sourceKey) {
                if (!isset($response[$sourceKey]) || !is_array($response[$sourceKey])) {
                    continue;
                }

                $items = array_values(array_filter(
                    $response[$sourceKey],
                    static fn ($item) => is_array($item)
                ));

                for ($i = 0; $i < 3 && $i < count($items); $i++) {
                    $slot = 'char' . ($i + 1);
                    if (!isset($response[$slot]) || !is_array($response[$slot])) {
                        $response[$slot] = $items[$i];
                    }
                }
            }

            return $response;
        }

        if (is_string($response) && trim($response) !== '') {
            $trimmed = trim($response);
            $decoded = json_decode($trimmed, true);
            if (is_array($decoded)) {
                return $this->normalizeTeamResponse($decoded);
            }

            // Do not surface malformed JSON-like blobs as team strategy text.
            if (str_starts_with($trimmed, '{') || str_starts_with($trimmed, '[')) {
                return [];
            }

            return ['strategy' => $trimmed];
        }

        return [];
    }

    /**
     * @param  array<string, mixed>  $team
     */
    private function hasVisibleTeamContent(array $team): bool
    {
        if (trim((string) ($team['strategy'] ?? '')) !== '') {
            return true;
        }

        foreach (['char1', 'char2', 'char3'] as $key) {
            if (!isset($team[$key]) || !is_array($team[$key])) {
                continue;
            }

            if (trim((string) ($team[$key]['name'] ?? '')) !== '') {
                return true;
            }
        }

        return false;
    }

    private function normalizeTextResponse(mixed $response): string
    {
        if (is_string($response)) {
            return trim($response);
        }

        if (is_array($response)) {
            if (isset($response['response'])) {
                return $this->normalizeTextResponse($response['response']);
            }

            if (isset($response['text']) && is_string($response['text'])) {
                return trim($response['text']);
            }
        }

        return '';
    }

    private function httpRequest(): PendingRequest
    {
        $request = Http::acceptJson();

        if ($this->apiKey !== null) {
            $request = $request->withHeaders([
                $this->apiKeyHeader => $this->apiKey,
            ]);
        }

        return $request;
    }

    /**
     * Seconds to wait for the Python API (LLM calls can be very slow on low-spec hosts).
     */
    private function httpTimeoutSeconds(): int
    {
        $t = (int) config('mkm.http_timeout_seconds', 3600);

        return max(60, $t);
    }

    private function pythonApiConnectionMessage(RequestException $e): string
    {
        $msg = $e->getMessage();
        if (preg_match('/timeout|timed out|cURL error 28|Operation timed out|Connection timed out|Failed to connect/i', $msg)) {
            return 'The Python assistant API did not finish within the HTTP time limit (slow LLM or CPU). '
                .'Increase MKM_HTTP_TIMEOUT_SECONDS in your environment (see config/mkm.php), then retry.';
        }

        return 'Cannot reach the MK Mobile assistant API. Make sure the Python server is running.';
    }
}
