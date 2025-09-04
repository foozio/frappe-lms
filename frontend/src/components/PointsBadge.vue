<template>
	<div
		:class="[
			'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium transition-colors',
			variant === 'primary' ? 'bg-blue-100 text-blue-800' :
			variant === 'success' ? 'bg-green-100 text-green-800' :
			variant === 'warning' ? 'bg-yellow-100 text-yellow-800' :
			variant === 'danger' ? 'bg-red-100 text-red-800' :
			'bg-gray-100 text-gray-800',
			size === 'sm' ? 'px-2 py-1 text-xs' :
			size === 'lg' ? 'px-4 py-2 text-base' : ''
		]"
	>
		<span v-if="showIcon" class="mr-1">{{ getIcon() }}</span>
		<span>{{ formatPoints(points) }}</span>
		<span class="ml-1 opacity-75">{{ points === 1 ? 'point' : 'points' }}</span>
	</div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	points: {
		type: Number,
		required: true
	},
	variant: {
		type: String,
		default: 'primary',
		validator: (value) => ['primary', 'success', 'warning', 'danger', 'gray'].includes(value)
	},
	size: {
		type: String,
		default: 'md',
		validator: (value) => ['sm', 'md', 'lg'].includes(value)
	},
	showIcon: {
		type: Boolean,
		default: true
	}
})

const formatPoints = (points) => {
	if (points >= 1000000) {
		return (points / 1000000).toFixed(1) + 'M'
	}
	if (points >= 1000) {
		return (points / 1000).toFixed(1) + 'K'
	}
	return points.toString()
}

const getIcon = () => {
	switch (props.variant) {
		case 'success': return '✨'
		case 'warning': return '⚡'
		case 'danger': return '🔥'
		default: return '💎'
	}
}
</script>