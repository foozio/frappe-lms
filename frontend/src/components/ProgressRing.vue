<template>
	<div class="relative inline-flex items-center justify-center">
		<svg
			:width="size"
			:height="size"
			class="transform -rotate-90"
		>
			<!-- Background circle -->
			<circle
				:cx="center"
				:cy="center"
				:r="radius"
				stroke="currentColor"
				:stroke-width="strokeWidth"
				fill="none"
				class="text-gray-200"
			/>
			<!-- Progress circle -->
			<circle
				:cx="center"
				:cy="center"
				:r="radius"
				stroke="currentColor"
				:stroke-width="strokeWidth"
				fill="none"
				:stroke-dasharray="circumference"
				:stroke-dashoffset="strokeDashoffset"
				:class="[
					'transition-all duration-500 ease-out',
					color === 'blue' ? 'text-blue-500' :
					color === 'green' ? 'text-green-500' :
					color === 'yellow' ? 'text-yellow-500' :
					color === 'red' ? 'text-red-500' :
					color === 'purple' ? 'text-purple-500' :
					'text-gray-500'
				]"
				stroke-linecap="round"
			/>
		</svg>
		
		<!-- Center content -->
		<div class="absolute inset-0 flex items-center justify-center">
			<div class="text-center">
				<div
					:class="[
						'font-bold',
						size >= 120 ? 'text-lg' :
						size >= 80 ? 'text-base' :
						'text-sm'
					]"
				>
					<slot name="center">
						{{ Math.round(percentage) }}%
					</slot>
				</div>
				<div
					v-if="showLabel && label"
					:class="[
						'text-gray-600 mt-1',
						size >= 120 ? 'text-xs' :
						size >= 80 ? 'text-xs' :
						'text-xs'
					]"
				>
					{{ label }}
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	percentage: {
		type: Number,
		required: true,
		validator: (value) => value >= 0 && value <= 100
	},
	size: {
		type: Number,
		default: 120
	},
	strokeWidth: {
		type: Number,
		default: 8
	},
	color: {
		type: String,
		default: 'blue',
		validator: (value) => ['blue', 'green', 'yellow', 'red', 'purple', 'gray'].includes(value)
	},
	label: {
		type: String,
		default: ''
	},
	showLabel: {
		type: Boolean,
		default: true
	},
	animated: {
		type: Boolean,
		default: true
	}
})

const center = computed(() => props.size / 2)
const radius = computed(() => (props.size - props.strokeWidth) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const strokeDashoffset = computed(() => {
	const progress = Math.min(Math.max(props.percentage, 0), 100)
	return circumference.value - (progress / 100) * circumference.value
})
</script>