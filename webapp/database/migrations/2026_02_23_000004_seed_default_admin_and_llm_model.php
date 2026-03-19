<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

return new class extends Migration
{
    public function up(): void
    {
        DB::table('users')->updateOrInsert(
            ['email' => 'admin@example.com'],
            [
                'name' => 'admin',
                'email_verified_at' => now(),
                'password' => Hash::make('MKadmin92'),
                'role' => 'admin',
                'created_at' => now(),
                'updated_at' => now(),
            ]
        );

        DB::table('llm_models')->updateOrInsert(
            ['slug' => 'llama3.2:3b'],
            [
                'name' => 'Llama 3.2',
                'slug' => 'llama3.2:3b',
                'parameter_size' => '3b',
                'provider' => 'ollama',
                'description' => 'Llama 3.2 3B — lightweight, fast inference model.',
                'is_active' => true,
                'created_at' => now(),
                'updated_at' => now(),
            ]
        );
    }

    public function down(): void
    {
        DB::table('users')->where('email', 'admin@example.com')->delete();
        DB::table('llm_models')->where('slug', 'llama3.2:3b')->delete();
    }
};
