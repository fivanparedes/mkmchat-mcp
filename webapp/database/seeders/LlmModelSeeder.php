<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class LlmModelSeeder extends Seeder
{
    public function run(): void
    {
        $models = [
            [
                'name'           => 'Mistral Nemo',
                'slug'           => 'mistral-nemo:12b',
                'parameter_size' => '12b',
                'provider'       => 'ollama',
                'description'    => 'Mistral Nemo 12B — strong general-purpose reasoning model.',
                'is_active'      => true,
                'created_at'     => now(),
                'updated_at'     => now(),
            ],
            [
                'name'           => 'Dolphin Llama 3',
                'slug'           => 'dolphin-llama3:8b',
                'parameter_size' => '8b',
                'provider'       => 'ollama',
                'description'    => 'Dolphin Llama 3 8B — uncensored fine-tune of Llama 3.',
                'is_active'      => true,
                'created_at'     => now(),
                'updated_at'     => now(),
            ],
            [
                'name'           => 'Llama 3.2',
                'slug'           => 'llama3.2:3b',
                'parameter_size' => '3b',
                'provider'       => 'ollama',
                'description'    => 'Llama 3.2 3B — lightweight, fast inference model.',
                'is_active'      => true,
                'created_at'     => now(),
                'updated_at'     => now(),
            ],
            [
                'name'           => 'DeepSeek R1 14B (Low Memory)',
                'slug'           => 'deepseek-r1:14b-fit',
                'parameter_size' => '14b',
                'provider'       => 'ollama',
                'description'    => 'DeepSeek R1 Distill 14B tuned for constrained RAM (num_ctx=512, num_batch=32, use_mmap=true).',
                'is_active'      => true,
                'created_at'     => now(),
                'updated_at'     => now(),
            ],
        ];

        foreach ($models as $model) {
            DB::table('llm_models')->updateOrInsert(
                ['slug' => $model['slug']],
                $model,
            );
        }
    }
}
