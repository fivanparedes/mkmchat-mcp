<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Schema;
use Tests\TestCase;

class ChatMigrationsTest extends TestCase
{
    use RefreshDatabase;

    public function test_chat_tables_exist_with_expected_columns(): void
    {
        $this->assertTrue(Schema::hasTable('conversations'));
        $this->assertTrue(Schema::hasColumns('conversations', [
            'id',
            'user_id',
            'title',
            'summary_text',
            'summary_message_count',
            'last_message_at',
            'created_at',
            'updated_at',
        ]));

        $this->assertTrue(Schema::hasTable('conversation_messages'));
        $this->assertTrue(Schema::hasColumns('conversation_messages', [
            'id',
            'conversation_id',
            'role',
            'content',
            'model_slug',
            'meta',
            'created_at',
            'updated_at',
        ]));
    }
}
