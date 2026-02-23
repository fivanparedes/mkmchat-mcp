<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class QueryHistory extends Model
{
    use HasFactory;

    protected $fillable = [
        'user_id',
        'query_type',
        'strategy',
        'owned_characters',
        'response',
        'status',
        'error_message',
        'model_slug',
    ];

    protected $casts = [
        'owned_characters' => 'array',
        'response'         => 'array',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Parse the three characters out of the response JSON.
     *
     * @return array<int, array{name:string,rarity:string,passive:string,equipment:array}>
     */
    public function characters(): array
    {
        if (empty($this->response)) {
            return [];
        }

        $chars = [];
        foreach (['char1', 'char2', 'char3'] as $key) {
            if (isset($this->response[$key])) {
                $chars[] = $this->response[$key];
            }
        }

        return $chars;
    }

    public function strategy(): string
    {
        return $this->response['strategy'] ?? '';
    }

    public function textResponse(): string
    {
        return $this->response['text'] ?? '';
    }
}
